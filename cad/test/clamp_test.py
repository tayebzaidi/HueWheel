"""Encoder clamp test: the plate's encoder socket with thinner uprights.
conda run -n base python cad/test/clamp_test.py

Not a production part. Three copies of the plate's encoder socket (U-slot upright, floor
ledge and side cheeks, at the real heights) in one bar. Each upright is a different
thickness, engraved on the slab in front of it. The encoder's threaded bushing has to
reach through the upright far enough for its own washer and nut.

Print it as exported, no supports, at 0.2 mm layers like the plate. For each socket:
1. Drop an encoder in, bushing through the U. Check it seats without forcing and doesn't
   twist or rattle between the cheeks (this checks the socket fits, which so far come
   only from the datasheet).
2. Put the washer and nut on the bushing from the front and tighten by hand, then a
   little with pliers. Count the full turns of thread the nut gets.
3. Check the upright doesn't crack or bend, and that the encoder is now rigid.
Report the thinnest upright that feels solid, and how many turns the nut got on each.
"""
import sys
from pathlib import Path

from build123d import Align, Plane, Text, export_stl, extrude

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import huewheel as hw  # noqa: E402

THICKNESS = (1.5, 2.0, 2.5)  # the plate's upright is 3.0 today
FRONT = 9.0           # slab in front of the upright, room for the label and the nut
SPACING = 22.0        # socket centres along Y
LABEL_SIZE = 4.0
LABEL_DEPTH = 0.6


def make_socket(t):
    """One socket in plate coordinates, axle along X, mounting face at x = MOUNT_X."""
    m = hw.MOUNT_X
    w, h = hw.ENC_BODY_W / 2, hw.ENC_BODY_H / 2
    back = m + hw.ENC_BODY_L + 0.5
    s = hw.bx(m - t - FRONT, back + 1, -SPACING / 2, SPACING / 2, 0, hw.PLATE_T)  # slab
    # upright with the U-slot, as u_cradle() in make_plate
    up = hw.bx(m - t, m, -10, 10, hw.PLATE_T, hw.CRADLE_TOP)
    slot = hw.ENC_BUSH_D + 0.3
    up -= hw.bx(m - t - 1, m + 1, -slot / 2, slot / 2, hw.AXIS_Z, hw.CRADLE_TOP + 1)
    up -= hw.cyl_x(m - t - 1, m + 1, slot)
    s += up
    # floor ledge and cheeks behind it, as in make_plate
    s += hw.bx(m, m + hw.ENC_LEDGE, -w - 2.5, w + 2.5, hw.PLATE_T, hw.AXIS_Z - h)
    for sy in (-1, 1):
        s += hw.bx(m, back, *sorted((sy * w, sy * (w + 2.5))), hw.PLATE_T, hw.AXIS_Z + h - 1)
    label = Text(f"{t:.1f}", font_size=LABEL_SIZE, font_path=hw.FONT_PATH,
                 align=(Align.CENTER, Align.CENTER))
    top = Plane(origin=(m - t - FRONT / 2, 0, hw.PLATE_T - LABEL_DEPTH), x_dir=(0, -1, 0), z_dir=(0, 0, 1))
    return s - top * extrude(label, amount=LABEL_DEPTH + 0.1)


def make_piece():
    piece = None
    for i, t in enumerate(THICKNESS):
        sock = hw.Pos(-hw.MOUNT_X, (i - (len(THICKNESS) - 1) / 2) * SPACING, 0) * make_socket(t)
        piece = sock if piece is None else piece + sock
    return piece


if __name__ == "__main__":
    piece = make_piece()
    bb = piece.bounding_box()
    out = Path(__file__).parent / "clamp_test.stl"
    print(f"clamp_test valid={piece.is_valid} vol={piece.volume / 1000:.2f} cm3 "
          f"z={bb.min.Z:.2f}..{bb.max.Z:.2f} size={tuple(round(v, 1) for v in bb.size)}")
    export_stl(piece, str(out), tolerance=0.01, angular_tolerance=0.1)
    print("wrote", out)
