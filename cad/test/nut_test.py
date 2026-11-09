"""Captive-nut slot test for the shell's corner bosses.  conda run -n base python cad/test/nut_test.py

Not a production part. Three bosses in one bar, each cut exactly like a shell corner:
the screw bore from the bed, a 2.6 mm shelf, the hex slot with its sideways mouth, and
the bridged hole above. NUT_SLOT_H is fixed at 2.6 mm (2.4 was too tight to load, 2.6 too
loose at the old width) and only the width across the flats changes: NUT_FIT is the
clearance over the nut's nominal 5.5 mm, engraved on the back face.

Print it as exported, no supports, at 0.2 mm layers like the shell. Slide an M3 nut into
each mouth. Pick the tightest one where the nut goes in by finger or with a light push
from a screwdriver and then stays put when you shake the piece. Then thread an M3 x 8 up
from the bed to check it pulls the nut down. Set NUT_FIT and NUT_SLOT_H in cad/huewheel.py.
"""
import sys
from pathlib import Path

from build123d import Align, Plane, Pos, Text, export_stl, extrude

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import huewheel as hw  # noqa: E402

FITS = (0.0, 0.1, 0.2)
SLOT_H = 2.6
FRONT = 4.5         # hole centre to the open face, as in the shell (36 - 31.5)
BACK = 5.0
HALF_W = 5.0
LABEL_SIZE = 3.0
LABEL_DEPTH = 0.5


def make_boss(fit):
    """One boss, bed at z=0, hole at x=y=0, mouth opening on the -X face."""
    z0 = hw.PLATE_T             # shell coordinates; shifted to the bed at the end
    top = hw.BORE_TOP
    af = hw.NUT_AF + fit
    boss = hw.bx(-FRONT, BACK, -HALF_W, HALF_W, z0, top)
    boss -= Pos(0, 0, (z0 - 1 + hw.NUT_Z) / 2) * hw.Cylinder(hw.BORE_D / 2, hw.NUT_Z - z0 + 1)
    boss -= Pos(0, 0, hw.NUT_Z) * hw.nut_hex(af, SLOT_H)
    boss -= hw.bridged_hole(0, 0, hw.NUT_Z + SLOT_H, top + 0.1, af, round_below=False)
    boss -= hw.bx(-FRONT - 1, 0, -af / 2, af / 2, hw.NUT_Z, hw.NUT_Z + SLOT_H)
    label = Text(f"{fit:.1f}", font_size=LABEL_SIZE, font_path=hw.FONT_PATH,
                 align=(Align.CENTER, Align.CENTER))
    face = Plane(origin=(BACK - LABEL_DEPTH, 0, (z0 + top) / 2), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    boss -= face * extrude(label, amount=LABEL_DEPTH + 0.1)
    return Pos(0, 0, -z0) * boss


def make_piece():
    piece = None
    for i, fit in enumerate(FITS):
        boss = Pos(0, (i - (len(FITS) - 1) / 2) * 2 * HALF_W, 0) * make_boss(fit)
        piece = boss if piece is None else piece + boss
    return piece


if __name__ == "__main__":
    piece = make_piece()
    bb = piece.bounding_box()
    out = Path(__file__).parent / "nut_test.stl"
    print(f"nut_test valid={piece.is_valid} vol={piece.volume / 1000:.2f} cm3 "
          f"z={bb.min.Z:.2f}..{bb.max.Z:.2f} size={tuple(round(v, 1) for v in bb.size)}")
    export_stl(piece, str(out), tolerance=0.01, angular_tolerance=0.1)
    print("wrote", out)
