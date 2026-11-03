"""Supportless-print check for cad/stl/*.stl (needs trimesh + shapely).

    python cad/printcheck.py [part ...]

Slices each part as it sits on the bed, layer by layer. Anything in a layer that is
more than a 45 degree step out from the layer below has nothing to print on. Those
areas pass only if they are bridges: straight lines in one direction that are
anchored at both ends and no longer than BRIDGE_MAX, or short ledges reaching no
more than LEDGE past the layer below. Prints PRINT CHECK PASSED or
lists each failing area with its height and position.
"""
import sys
from pathlib import Path

import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import unary_union

LAYER = 0.2
STEP = LAYER          # 45 degrees: each layer may step out one layer height
ANCHOR = 0.3          # a bridge line end within this of the layer below counts as anchored
BRIDGE_MAX = 50.0     # longest bridge the slicer is trusted with (mm)
MIN_AREA = 0.3        # ignore slivers smaller than this (mm2)
LEDGE = 0.8           # a ledge reaching no further than this past the layer below is fine:
                      # the 0.7 mm deep numerals on the wheels printed cleanly, while the
                      # first plate's 1.4 mm counterbore ledges did not
CHAIN = 4             # ...but not when it sits mostly on the previous layer's ledge, and that on
                      # another, for more than this many layers: that is a shallow ceiling
                      # (the first shell's 15 degree deck failed this way)
ROOT = Path(__file__).parent


def polys(mesh, z):
    sec = mesh.section(plane_origin=(0, 0, z), plane_normal=(0, 0, 1))
    if sec is None:
        return Polygon()
    planar, to_3d = sec.to_2D()
    shapes = [affinity.affine_transform(p, [to_3d[0, 0], to_3d[0, 1], to_3d[1, 0], to_3d[1, 1],
                                            to_3d[0, 3], to_3d[1, 3]]) for p in planar.polygons_full]
    return unary_union(shapes).buffer(0)


def bridge_ok(region, support):
    """Best single direction: share of the region's area whose lines are anchored both
    ends, and the longest such line."""
    best = (0.0, 0.0)
    cx, cy = region.centroid.x, region.centroid.y
    for ang in range(0, 180, 15):
        r = affinity.rotate(region, -ang, origin=(cx, cy))
        s = affinity.rotate(support, -ang, origin=(cx, cy)).buffer(ANCHOR)
        x0, y0, x1, y1 = r.bounds
        good = total = 0.0
        longest = 0.0
        for y in np.arange(y0 + 0.1, y1, 0.2):
            hit = r.intersection(LineString([(x0 - 1, y), (x1 + 1, y)]))
            for seg in getattr(hit, "geoms", [hit]):
                if seg.is_empty or seg.length < 1e-6:
                    continue
                a, b = seg.coords[0], seg.coords[-1]
                total += seg.length
                if s.contains(Polygon([(a[0] - .01, a[1] - .01), (a[0] + .01, a[1] - .01), (a[0], a[1] + .01)])) and \
                   s.contains(Polygon([(b[0] - .01, b[1] - .01), (b[0] + .01, b[1] - .01), (b[0], b[1] + .01)])):
                    good += seg.length
                    longest = max(longest, seg.length)
        if total and good / total > best[0]:
            best = (good / total, longest)
    return best


def check(name):
    mesh = trimesh.load(ROOT / "stl" / f"{name}.stl")
    top = mesh.bounds[1][2]
    prev = None
    prev_ledges = []      # (region, chain depth) of the layer below
    fails, bridges, ledges = [], [], 0
    for z in np.arange(LAYER / 2, top, LAYER):
        cur = polys(mesh, z)
        cur_ledges = []
        if prev is not None and not cur.is_empty:
            raw = cur.difference(prev.buffer(STEP))
            loose = raw.buffer(-0.1).buffer(0.1)  # find pieces wider than ~0.2 mm
            for g in getattr(loose, "geoms", [loose]):
                if g.is_empty or g.area < MIN_AREA:
                    continue
                where = f"z={z - LAYER / 2:5.1f} at ({g.centroid.x:6.1f}, {g.centroid.y:6.1f}) area {g.area:6.1f} mm2"
                beyond = g.difference(prev.buffer(STEP + LEDGE))
                if beyond.area < MIN_AREA:
                    border = prev.intersection(g.buffer(STEP + 0.3))
                    under = [(r, d) for r, d in prev_ledges if r.intersects(border)]
                    on_ledge = unary_union([r for r, _ in under]).intersection(border).area if under else 0.0
                    depth = 1 + max(d for _, d in under) if border.area and on_ledge > 0.5 * border.area else 1
                    cur_ledges.append((g, depth))
                    if depth == CHAIN + 1:
                        fails.append(f"{where}  shallow overhang: ledge on ledge for {depth} layers")
                    elif depth <= CHAIN:
                        ledges += 1
                    continue
                # judge the untrimmed piece: trimming pulls its ends off their anchors
                share, span = bridge_ok(raw.intersection(g.buffer(0.15)), prev)
                if share >= 0.9 and span <= BRIDGE_MAX:
                    bridges.append(f"{where}  bridge {span:4.1f} mm")
                else:
                    fails.append(f"{where}  {share:4.0%} anchored both ends, longest {span:4.1f} mm")
        prev, prev_ledges = cur, cur_ledges
    print(f"{name}: {ledges} short ledges, {len(bridges)} bridges, {len(fails)} unsupported")
    for b in bridges:
        print("   ok  ", b)
    for f in fails:
        print("   FAIL", f)
    return not fails


if __name__ == "__main__":
    names = sys.argv[1:] or ["plate", "shell", "wheel_hours", "wheel_minutes"]
    ok = all([check(n) for n in names])
    print("PRINT CHECK", "PASSED" if ok else "FAILED")
