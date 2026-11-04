"""Heat-set insert test block.  conda run -n base python cad/test/insert_test.py

Not a production part. Five M3 x 6 insert holes, 3.8 to 4.2 mm, each built exactly like
the holes in the shell's corner bosses (same chamfer, depth and cone roof) and opening
on the bed face as they do in the shell. The hole size is engraved on the top above each.

Print it as exported (engraved face up), 0.2 mm layers, no supports. Flip it over, press
an insert into each hole with the iron, let it cool, then thread in an M3 screw. Use the
smallest hole that took the insert without cracking or bulging the wall, and still holds
when you tighten the screw firmly. Set INSERT_HOLE_D in cad/huewheel.py to that size.
"""
import sys
from pathlib import Path

from build123d import Align, Pos, Text, export_stl, extrude

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import huewheel as hw  # noqa: E402

SIZES = (3.8, 3.9, 4.0, 4.1, 4.2)
PITCH = 9.0      # leaves about the same wall as the shell's corner bosses
DEPTH_Y = 10.0
HEIGHT = 13.0
LABEL_SIZE = 3.6
LABEL_DEPTH = 0.6


def make_block():
    length = PITCH * len(SIZES)
    block = hw.bx(-length / 2, length / 2, -DEPTH_Y / 2, DEPTH_Y / 2, 0, HEIGHT)
    for i, d in enumerate(SIZES):
        x = (i - (len(SIZES) - 1) / 2) * PITCH
        block -= hw.insert_hole(x, 0, 0, d)
        label = Text(f"{d:.1f}", font_size=LABEL_SIZE, font_path=hw.FONT_PATH,
                     align=(Align.CENTER, Align.CENTER))
        block -= Pos(x, 0, HEIGHT - LABEL_DEPTH) * extrude(label, amount=LABEL_DEPTH + 0.1)
    return block


if __name__ == "__main__":
    block = make_block()
    out = Path(__file__).parent / "insert_test.stl"
    print(f"insert_test valid={block.is_valid} vol={block.volume / 1000:.1f} cm3")
    export_stl(block, str(out), tolerance=0.02, angular_tolerance=0.15)
    print("wrote", out)
