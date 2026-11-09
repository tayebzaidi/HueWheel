"""Crush-rib test piece for the wheel's D bore.  conda run -n base python cad/test/rib_test.py

Not a production part. Three hubs in one bar, each with the wheel's encoder bore cut
exactly as in the wheels (pocket, cone lead-in, D bore) but with a different rib size:
how far each rib reaches into the seated shaft. The size is engraved on the front.
It opens through the top so you can see the shaft tip.

Print it as exported (bed face down, like the wheels' outer face), no supports, at the
wheels' layer height. Push an encoder shaft into each hub from the bed side, flat
first, and pull it out again. Pick the tightest one that goes all the way on by hand
without cracking and has no wobble or turning play. Set RIB_I in cad/huewheel.py to it.
"""
import sys
from pathlib import Path

from build123d import Align, Plane, Pos, Rot, Text, export_stl, extrude

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import huewheel as hw  # noqa: E402

RIBS = (0.1, 0.2, 0.3)
HUB = 16.0          # hub width around the bore
X_TOP = hw.BORE_END + 0.1   # the bore runs out through the top
X_BED = 14.0        # inside the wheel's bushing pocket, so the cone lead-in is included
LABEL_SIZE = 3.6
LABEL_DEPTH = 0.5


def make_hub(rib):
    """One hub cut from the right-hand wheel's geometry, in the wheel's own frame."""
    block = hw.bx(X_TOP, X_BED, -HUB / 2, HUB / 2, hw.AXIS_Z - HUB / 2, hw.AXIS_Z + HUB / 2)
    return block - hw.wheel_bore(-1, rib)


def make_piece():
    piece = None
    for i, rib in enumerate(RIBS):
        # stand the hub up: the outer (pocket) side on the bed, bore axis vertical
        hub = Pos(0, 0, X_BED) * Rot(0, 90, 0) * Pos(0, 0, -hw.AXIS_Z) * make_hub(rib)
        y = (i - (len(RIBS) - 1) / 2) * HUB
        hub = Pos(0, y, 0) * hub
        label = Text(f"{rib:.1f}", font_size=LABEL_SIZE, font_path=hw.FONT_PATH,
                     align=(Align.CENTER, Align.CENTER))
        h = X_BED - X_TOP
        # engraved on the front face (-X once stood up)
        face = Plane(origin=(-HUB / 2 + LABEL_DEPTH, y, h / 2), x_dir=(0, -1, 0), z_dir=(-1, 0, 0))
        hub -= face * extrude(label, amount=LABEL_DEPTH + 0.1)
        piece = hub if piece is None else piece + hub
    return piece


if __name__ == "__main__":
    piece = make_piece()
    bb = piece.bounding_box()
    out = Path(__file__).parent / "rib_test.stl"
    print(f"rib_test valid={piece.is_valid} vol={piece.volume / 1000:.2f} cm3 "
          f"z={bb.min.Z:.2f}..{bb.max.Z:.2f} size={tuple(round(v, 1) for v in bb.size)}")
    export_stl(piece, str(out), tolerance=0.01, angular_tolerance=0.1)
    print("wrote", out)
