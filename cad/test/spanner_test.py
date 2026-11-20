"""Thin spanners for the encoder nut.  conda run -n base python cad/test/spanner_test.py

Not a production part, but a keeper if one fits: the encoder's nut sits in the 3.5 mm gap
between the wheel and the plate's upright, where fingers can't reach. A spanner thinner
than the nut drops into the gap from above, jaws around the nut, and swings in the gap.

The nut hasn't been measured, so this prints four guesses at its size across the flats,
each engraved on its handle. The jaw is that size plus JAW_CLEAR. Print flat as exported,
no supports, at 0.2 mm layers. Try them on a loose nut first: pick the one that slides on
with no rock. Then check it drops into the gap beside a seated wheel and turns the nut.
"""
import sys
from pathlib import Path

from build123d import Align, Plane, Pos, Text, export_stl, extrude

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import huewheel as hw  # noqa: E402

SIZES = (9.0, 9.5, 10.0, 11.0)  # guesses at the nut across the flats; ISO M7 is 11, panel nuts often smaller
THICK = 1.6          # under the nut's thickness, and leaves room in the 3.5 mm gap
JAW_CLEAR = 0.2      # printed slots come out a little small
JAW_WALL = 4.5       # each jaw cheek
HANDLE_L = 55.0      # nut centre to handle end
HANDLE_W = 9.0
LABEL_SIZE = 4.5
LABEL_DEPTH = 0.4
SPACING = 26.0


def make_spanner(af):
    """Flat on the bed, nut centre at the origin, mouth facing -X, handle along +X."""
    w = af + JAW_CLEAR
    centre = 0.55 * af                 # nut centre this far in from the mouth: both flats engaged
    back = centre + af / 3 ** 0.5 + 0.3  # clears the hex corner pointing into the jaw
    head = hw.bx(-centre, back - centre + JAW_WALL, -w / 2 - JAW_WALL, w / 2 + JAW_WALL, 0, THICK)
    head -= hw.bx(-centre - 1, back - centre, -w / 2, w / 2, -1, THICK + 1)
    handle = hw.bx(back - centre, HANDLE_L, -HANDLE_W / 2, HANDLE_W / 2, 0, THICK)
    s = head + handle
    label = Text(f"{af:.1f}", font_size=LABEL_SIZE, font_path=hw.FONT_PATH,
                 align=(Align.CENTER, Align.CENTER))
    top = Plane(origin=((back - centre + JAW_WALL + HANDLE_L) / 2, 0, THICK - LABEL_DEPTH))
    return s - top * extrude(label, amount=LABEL_DEPTH + 0.1)


def make_piece():
    piece = None
    for i, af in enumerate(SIZES):
        s = Pos(0, (i - (len(SIZES) - 1) / 2) * SPACING, 0) * make_spanner(af)
        piece = s if piece is None else piece + s
    return piece


if __name__ == "__main__":
    piece = make_piece()
    bb = piece.bounding_box()
    out = Path(__file__).parent / "spanner_test.stl"
    print(f"spanner_test valid={piece.is_valid} vol={piece.volume / 1000:.2f} cm3 "
          f"z={bb.min.Z:.2f}..{bb.max.Z:.2f} size={tuple(round(v, 1) for v in bb.size)}")
    export_stl(piece, str(out), tolerance=0.01, angular_tolerance=0.1)
    print("wrote", out)
