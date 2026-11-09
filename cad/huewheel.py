"""HueWheel enclosure - parametric build123d model.

Run with the conda base env:  conda run -n base python cad/huewheel.py

Frame: X = left/right, Y = front(-)/rear(+), Z = up.
Wheel axle runs along X through (y=0, z=AXIS_Z), like a mouse scroll wheel.
Rim angles (phi) are measured from +Z towards the front (-Y).
"""
from math import asin, atan2, cos, degrees, hypot, radians, sin
from pathlib import Path

from build123d import (
    Align, Axis, Box, BuildLine, BuildSketch, Circle, Cone, Cylinder, FontStyle,
    Line, Plane, Pos, Rectangle, RectangleRounded, RegularPolygon, Rot, Sketch, Text,
    ThreePointArc, chamfer, export_step, export_stl, extrude, fillet, make_face,
)

# ---- edit these once real parts are measured -------------------------------
BASE = 84.0            # square footprint
CORNER_R = 5.0
PLATE_T = 3.5          # base plate thickness
PLINTH_TOP = 16.0      # height where the square plinth starts to taper
WALL = 2.4

N_POS = 24             # must equal the encoder's detents per revolution
WHEEL_R = 22.0
WHEEL_W = 14.0
WHEEL_IN = 3.5         # |x| of each wheel's inner face
AXIS_Z = 30.0
SHELL_R = 25.4         # outer radius of the hump (concentric with wheels)
TOP_HALF = 36.0        # shell half-width at the top of the hump

GRIP_W = 3.0           # ribbed band on each edge of the rim (the "notching")
GRIP_CUT_R = 1.4
TEXT_SIZE = 6.5
TEXT_DEPTH = 0.7
FONT = "Liberation Sans"
FONT_PATH = "/usr/share/fonts/liberation/LiberationSans-Bold.ttf"  # falls back to FONT

# Encoder: Bourns PEC11R-42xxF, dimensions from the Bourns datasheet (rev 04/26)
ENC_SHAFT_D = 6.0
ENC_SHAFT_FLAT = 4.5   # across the D
ENC_SHAFT_L = 15.0     # from mounting face
ENC_FLAT_L = 7.0       # the D-flat covers only this much of the shaft tip
ENC_BUSH_D = 7.0       # M7 x 0.75
ENC_BUSH_L = 5.0
ENC_BODY_W = 14.6      # socket across the side tabs (14.0 part + clearance), along Y
ENC_BODY_H = 13.8      # socket height (13.4 part + clearance), along Z
ENC_BODY_L = 6.5       # mounting face to rear of body
ENC_PIN_L = 3.7        # rear-facing pins, row 7.5 mm below the axle
ENC_LEDGE = 4.0        # how far the floor runs under the body; pins hang past it
FIT = 0.15             # radial clearance on the D bore
# Crush ribs in the D bore: three ridges that the shaft squashes as the wheel goes on,
# for a tight fit that still pulls off. One sits opposite the flat and pushes the shaft's
# flat onto the bore's, so the wheel has no turning play. RIB_I is how far each rib
# reaches into the shaft once seated; pick it with cad/test/rib_test.stl.
RIB_I = 0.2
RIB_W = 1.0
RIB_ANGLES = (180.0, 105.0, -105.0)  # degrees from the flat; the round wall starts at +/-60
CLOCK_OFFSET_DEG = 0.0 # rotate the D bore if numerals sit off-centre at a click

WINDOW_PHI = 50.0      # reading window, degrees forward of vertical
SLOT_PHI = (-58.0, 24.0)  # thumb slot
DECK_PHI = -15.0       # flat thumb deck: tilt back from vertical
DECK_D = 19.0          # deck height above axle; WHEEL_R - DECK_D = how proud the wheels stand

MCU_W, MCU_L, MCU_T = 17.8, 21.0, 1.3   # Seeed XIAO ESP32C3 (thickness from a user report, not Seeed)
SCREW_XY = 36.0
SCREW_L = 8.0          # M3 x 8 button head, Mywish kit
SCREW_HEAD_D, SCREW_HEAD_H = 5.7, 1.65  # ISO 7380 nominal
CBORE_D, CBORE_DEPTH = 6.2, 2.4
NUT_AF, NUT_H = 5.5, 2.4       # ISO 4032 M3 nut, nominal
NUT_FIT = 0.2          # slot clearance across the flats
NUT_SLOT_H = 2.4       # one 0.2 mm layer less than the 2.6 that printed loose; the bridged roof sags a little
NUT_Z = PLATE_T + 2.6  # underside of the nut: 2.6 mm shelf below it; keeps the slot roof on a 0.2 mm layer line
BORE_D = 3.4           # screw clearance through the plate and boss
BORE_TOP = PLATE_T + 8.5
LED_D = 5.0            # 5 mm through-hole LED; 3.0 for 3 mm LEDs
LED_LEN = 8.6          # base flange to dome tip (5.3 for 3 mm LEDs)
LED_BORE = LED_D + 0.3
LED_TIP_BACK = 20.0    # dome tip's distance back from where the slope meets the hump
LED_SLOT_TOP = -1.0   # slot walls end this far behind the dome tip
LED_SLOT_DEPTH = 4.0  # how far the slot walls reach in from the LED axis (LED radius + 1.5)
LIP_H, LIP_W = 2.0, 1.2    # locating lip on the plate, just inside the shell wall
LIP_GAP = 0.4          # clearance from the lip to the shell
SW_Y, SW_Z = -15.0, 10.25  # E-Switch EG1201A centre on the right wall

# Printability: everything prints without supports. Hanging features are flat-bottomed
# beams that bridge wall to wall, and screw holes use the two-layer bridging trick.
LAYER = 0.2            # slicer layer height the bridging tricks are built for
CRADLE_TOP = AXIS_Z + 3.9  # plate U-cradles stop here; the shell caps them
CAP_GAP = 0.2          # shell underside above the cradle tops
ENC_CAP_Z = AXIS_Z + 7.2   # shell underside above the encoder bodies (0.5 mm clear)
BULK_X0 = WHEEL_IN + WHEEL_W + 0.5  # inner face of the bulkhead over each encoder
FIN_T = 2.4           # LED slot walls (1.6 mm peeled off the bed on the third print)
RIB_T = 3.0           # front centre rib
FOOT_W, FOOT_H = 1.5, 1.0  # flange on each side of the thin walls' first 1 mm, for bed grip

HOURS = [f"{h:02d}" for h in range(24)]                     # 1 click = 1 hour
MINUTES = [f"{m:02d}" for m in range(0, 60, 5)] * 2         # 1 click = 5 min

# ---- derived ---------------------------------------------------------------
HALF = BASE / 2
WHEEL_OUT = WHEEL_IN + WHEEL_W
UPRIGHT = (WHEEL_OUT + 0.5, WHEEL_OUT + 3.5)
MOUNT_X = UPRIGHT[1]                  # encoder mounting face
BORE_END = MOUNT_X - ENC_SHAFT_L - 0.5
PITCH = 360.0 / N_POS


def nut_hex(across_flats, height):
    """Hexagonal prism with flats facing +/-Y, base at z=0."""
    return extrude(RegularPolygon(across_flats / 3 ** 0.5, 6), amount=height)


def bx(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box from min/max coordinates."""
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def bridged_hole(x, y, z0, z1, below_d, round_below=True):
    """BORE_D hole from z0 up to z1, starting above a wider recess (diameter below_d)
    without supports: one layer that leaves a BORE_D-wide strip open along Y, which
    prints as two bridges spanning Y; then one layer with a square BORE_D hole, whose
    two new edges bridge across the strip in X; then the round hole."""
    h = BORE_D / 2
    strip = bx(x - h, x + h, y - below_d / 2, y + below_d / 2, z0 - 0.01, z0 + LAYER)
    if round_below:
        strip &= Pos(x, y, z0) * Cylinder(below_d / 2, 2 * LAYER + 0.1)
    square = bx(x - h, x + h, y - h, y + h, z0, z0 + 2 * LAYER)
    return strip + square + Pos(x, y, (z0 + 2 * LAYER + z1) / 2) * Cylinder(h, z1 - z0 - 2 * LAYER + 0.01)


def foot(x0, x1, y0, y1):
    """Bed flange widening a thin wall's first FOOT_H mm by FOOT_W on each side in X.
    Stepping in above it is never an overhang."""
    return bx(x0 - FOOT_W, x1 + FOOT_W, y0, y1, PLATE_T, PLATE_T + FOOT_H)


def cyl_x(x0, x1, d, y=0.0, z=AXIS_Z):
    """Cylinder along X."""
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(d / 2, abs(x1 - x0))


def rim(phi, r):
    """(y, z) of a rim point at angle phi and radius r."""
    return -r * sin(radians(phi)), AXIS_Z + r * cos(radians(phi))


def tent_profile(half, r, z_bottom, z_plinth):
    """YZ profile: square plinth rising tangentially into a round hump."""
    dy, dz = half, AXIS_Z - z_plinth
    d = hypot(dy, dz)
    t = radians(degrees(atan2(dy, -dz)) - degrees(asin(1)) + degrees(asin(r / d)))
    p = (-r * sin(t), AXIS_Z + r * cos(t))
    with BuildSketch(Plane.YZ) as s:
        with BuildLine():
            Line((-half, z_bottom), (-half, z_plinth))
            Line((-half, z_plinth), p)
            ThreePointArc(p, (0, AXIS_Z + r), (-p[0], p[1]))
            Line((-p[0], p[1]), (half, z_plinth))
            Line((half, z_plinth), (half, z_bottom))
            Line((half, z_bottom), (-half, z_bottom))
        make_face()
    return s.sketch


def side_taper(half, z_bottom, z_top):
    """XZ profile: vertical plinth then taper to TOP_HALF - (HALF - half)."""
    top = TOP_HALF - (HALF - half)
    with BuildSketch(Plane.XZ) as s:
        with BuildLine():
            Line((-half, z_bottom), (-half, PLINTH_TOP))
            Line((-half, PLINTH_TOP), (-top, z_top))
            Line((-top, z_top), (top, z_top))
            Line((top, z_top), (half, PLINTH_TOP))
            Line((half, PLINTH_TOP), (half, z_bottom))
            Line((half, z_bottom), (-half, z_bottom))
        make_face()
    return s.sketch


def led_axis():
    """Point and unit direction (y, z) of the LED beam, along the inside of the front slope."""
    half, r = HALF - WALL, SHELL_R - WALL
    dy, dz = half, AXIS_Z - PLINTH_TOP
    d = hypot(dy, dz)
    t = radians(degrees(atan2(dy, -dz)) - 90 + degrees(asin(r / d)))
    p = (-r * sin(t), AXIS_Z + r * cos(t))
    uy, uz = p[0] + half, p[1] - PLINTH_TOP
    n = hypot(uy, uz)
    uy, uz = uy / n, uz / n
    a = SHELL_R - 1.2 - LED_BORE / 2  # keeps 1.2 mm of wall outside the bore
    foot = (-a * sin(t), AXIS_Z + a * cos(t))
    tip = (foot[0] - LED_TIP_BACK * uy, foot[1] - LED_TIP_BACK * uz)
    return tip, (uy, uz)


def led_cyl(x, d, s0, s1):
    """Cylinder on the LED axis, s measured along the beam from the dome tip."""
    tip, u = led_axis()
    origin = (x, tip[0] + s0 * u[0], tip[1] + s0 * u[1])
    return Plane(origin=origin, x_dir=(1, 0, 0), z_dir=(0, u[0], u[1])) * Pos(0, 0, (s1 - s0) / 2) * Cylinder(d / 2, s1 - s0)


def led_frame(s0=0.0):
    """Plane on the LED axis at s0 from the dome tip: local z along the beam, local y
    pointing away from the slope wall, into the shell."""
    tip, u = led_axis()
    return Plane(origin=(0, tip[0] + s0 * u[0], tip[1] + s0 * u[1]), x_dir=(1, 0, 0), z_dir=(0, u[0], u[1]))


def body_solid(half, r, z_bottom):
    z_top = AXIS_Z + SHELL_R + 2
    a = extrude(tent_profile(half, r, z_bottom, PLINTH_TOP), amount=HALF + 1, both=True)
    b = extrude(side_taper(half, z_bottom, z_top), amount=HALF + 1, both=True)
    plan = extrude(Plane.XY.offset(z_bottom) * RectangleRounded(2 * half, 2 * half,
                   max(CORNER_R - (HALF - half), 1.0)), amount=z_top)
    solid = a & b & plan
    # flat thumb deck, so the wheels stand proud like a mouse wheel
    d = DECK_D - (HALF - half)
    return solid - Pos(0, 0, AXIS_Z) * Rot(DECK_PHI, 0, 0) * bx(-60, 60, -80, 80, d, d + 80)


def sector(phi0, phi1, x0, x1, r0=15.0, r1=46.0):
    pts = [rim(phi0, r0), rim(phi0, r1), rim(phi1, r1), rim(phi1, r0)]
    with BuildSketch(Plane.YZ.offset(x0)) as s:
        with BuildLine():
            for a, b in zip(pts, pts[1:] + pts[:1]):
                Line(a, b)
        make_face()
    return extrude(s.sketch, amount=x1 - x0)


def make_shell():
    outer = body_solid(HALF, SHELL_R, PLATE_T)
    try:
        ridge = outer.edges().filter_by_position(Axis.Z, PLINTH_TOP + 1, 200)
        outer = fillet(ridge, 2.0)
    except Exception as exc:  # cosmetic only
        print("shell fillet skipped:", exc)
    inner = body_solid(HALF - WALL, SHELL_R - WALL, PLATE_T - 1)
    shell = outer - inner

    # screw bosses in the four corners
    b0, b1 = SCREW_XY - 4.5, HALF - WALL + 0.5
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = sorted((sx * b0, sx * b1))
            y = sorted((sy * b0, sy * b1))
            shell += bx(*x, *y, PLATE_T, PLATE_T + 12)

    # Retainers. Each one fills the shell from wall to wall above a flat, horizontal
    # underside, so the slicer prints that underside as a bridge between the front and
    # rear walls instead of an unsupported overhang. They stop the wheels and encoders
    # lifting out of the plate's U-cradles.
    # Below each cap, a wall rises from the bed and runs out to the front and rear outer
    # walls, leaving a window where the plate's cradle sits. The cap bridges only that
    # window, and no part of the wall stands alone on the bed (free-standing pillars
    # here fell over on the second print).
    cap = CRADLE_TOP + CAP_GAP
    xw = (-WHEEL_IN + 0.5, WHEEL_IN - 0.5)
    shell += outer & bx(*xw, -HALF, HALF, cap, 100)   # centre web
    shell += bx(*xw, -12.5, -9.5, PLATE_T, cap + 1)   # front: post beside the cradle...
    shell += outer & (bx(-RIB_T / 2, RIB_T / 2, -HALF, -9.5, PLATE_T, cap + 1)  # ...and a rib out to the wall
                      + foot(-RIB_T / 2, RIB_T / 2, -HALF, -12.5))
    # rear: the board and USB-C plug sit behind, so the wall arches over them. A short
    # post stands in front of the board's stop; the tunnel roof bridges post to rear wall.
    mcu_y0 = HALF - WALL - MCU_L - 1.0
    tunnel = bx(-MCU_W / 2 - 0.5, MCU_W / 2 + 0.5, mcu_y0 - 2.2, HALF + 1, PLATE_T - 1, 15.0)
    shell += (outer & bx(*xw, 9.5, HALF, PLATE_T, cap + 1)) - tunnel
    for s in (-1, 1):
        # over the encoder upright: low enough to cap the bushing in its U
        xb = sorted((s * BULK_X0, s * (MOUNT_X - 0.25)))
        # feet flare outward only: the wheels pass the inner face as the shell goes on
        xbf = sorted((s * BULK_X0, s * (MOUNT_X - 0.25 + FOOT_W)))
        shell += outer & bx(*xb, -HALF, HALF, cap, 100)
        shell += outer & (bx(*xb, -HALF, -10.5, PLATE_T, cap + 1) + bx(*xbf, -HALF, -10.5, PLATE_T, PLATE_T + FOOT_H))
        # rear: a doorway at the bottom passes the encoder and switch wires to the board
        door = bx(xb[0] - FOOT_W - 1, xb[1] + FOOT_W + 1, 16.0, 30.0, PLATE_T - 1, 9.0)
        shell += (outer & (bx(*xb, 10.5, HALF, PLATE_T, cap + 1) + bx(*xbf, 10.5, HALF, PLATE_T, PLATE_T + FOOT_H))) - door
        # over the encoder body, out to the side wall: replaces the tilted deck ceiling
        shell += outer & bx(*sorted((s * (MOUNT_X - 0.25), s * HALF)), -HALF, HALF, ENC_CAP_Z, 100)

    # LED slots on the inside of the front slope, one aimed up at each window. Two
    # walls rise from the bed beside each LED and join the front wall; the slot between
    # them is open towards the inside of the shell, so the LED drops in from there and
    # slides up until its base flange meets the step where the slot narrows.
    w_flange, w_body = (LED_D + 1.1) / 2, LED_BORE / 2
    for s in (-1, 1):
        xc = s * (WHEEL_IN + WHEEL_OUT) / 2
        reach = led_frame() * Pos(0, (LED_SLOT_DEPTH - 50) / 2, (LED_SLOT_TOP - 200) / 2) * Box(
            400, LED_SLOT_DEPTH + 50, LED_SLOT_TOP + 200)  # wall side of the slot, below its top
        stop = led_frame(-LED_LEN) * Pos(0, 0, -100) * Box(400, 400, 200)  # below the flange seat
        for d in (-1, 1):
            xf = sorted((xc + d * w_flange, xc + d * (w_flange + FIN_T)))
            xft = sorted((xc + d * w_flange, xc + d * (w_flange + FIN_T + FOOT_W)))  # foot flares outward only
            wall = bx(*xf, -HALF, HALF, PLATE_T, 100) + bx(*xft, -HALF, HALF, PLATE_T, PLATE_T + FOOT_H)
            step = bx(*sorted((xc + d * w_body, xc + d * w_flange)), -HALF, HALF, PLATE_T, 100) - stop
            shell += (wall + step) & reach & outer
        shell -= led_cyl(xc, LED_BORE, -LED_LEN - 2, 1)                    # groove in the slope wall
        shell -= led_cyl(xc, LED_D + 1.1, -LED_LEN - 4, -LED_LEN)          # ...wider for the flange

    # thumb slots + reading windows
    for s in (-1, 1):
        x = sorted((s * (WHEEL_IN - 0.25), s * (WHEEL_OUT + 0.25)))
        shell -= sector(*SLOT_PHI, *x)
        shell -= cyl_x(*x, 2 * (WHEEL_R + 0.9))  # rim clearance under the deck (not == inner hump R: coincident faces break the boolean)
        xc = s * (WHEEL_IN + WHEEL_OUT) / 2
        hw = (WHEEL_W - 2 * GRIP_W) / 2 + 0.2
        shell -= sector(WINDOW_PHI - PITCH / 2, WINDOW_PHI + PITCH / 2, xc - hw, xc + hw)
        # 45 degree flare so the numbers stay visible from low and side angles
        r0 = (SHELL_R - WALL) * cos(radians(PITCH / 2))
        y0, z0 = rim(WINDOW_PHI, r0)
        n = (0, -sin(radians(WINDOW_PHI)), cos(radians(WINDOW_PHI)))
        face = Plane(origin=(xc, y0, z0), x_dir=(1, 0, 0), z_dir=n)
        half_h = (SHELL_R - WALL) * sin(radians(PITCH / 2))
        shell -= extrude(face * Rectangle(2 * hw, 2 * half_h), amount=4.0, taper=-45)

    # colon between HH and MM
    for d in (-3.2, 3.2):
        y, z = rim(WINDOW_PHI + d, SHELL_R)
        n = Plane(origin=(0, y, z), z_dir=(0, -sin(radians(WINDOW_PHI + d)), cos(radians(WINDOW_PHI + d))))
        shell -= n * Pos(0, 0, -0.5) * Cylinder(0.9, 2.0)

    # USB-C notch (rear) and alarm on/off slide switch (right side)
    shell -= bx(-6.5, 6.5, HALF - WALL - 1, HALF + 1, PLATE_T - 1, PLATE_T + 10)
    shell -= bx(HALF - WALL - 1, HALF + 1, SW_Y - 4.5, SW_Y + 4.5, SW_Z - 2.25, SW_Z + 2.25)

    # captive M3 nuts: each slides into its boss from inside the shell. The screw
    # pulls the nut down onto the shelf below it, clamping the shell to the plate.
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * SCREW_XY, sy * SCREW_XY
            shell -= Pos(x, y, (PLATE_T - 1 + NUT_Z) / 2) * Cylinder(BORE_D / 2, NUT_Z - PLATE_T + 1)
            shell -= Pos(x, y, NUT_Z) * nut_hex(NUT_AF + NUT_FIT, NUT_SLOT_H)
            shell -= bridged_hole(x, y, NUT_Z + NUT_SLOT_H, BORE_TOP, NUT_AF + NUT_FIT, round_below=False)
            mouth = sorted((x, sx * (SCREW_XY - 6)))
            shell -= bx(*mouth, y - (NUT_AF + NUT_FIT) / 2, y + (NUT_AF + NUT_FIT) / 2, NUT_Z, NUT_Z + NUT_SLOT_H)
    return shell


def plate_lip(shell):
    """Low lip just inside the shell wall that seats the shell on the plate. It runs
    along each side between the corner bosses and steps around every shell wall, foot
    and fin that comes down to the plate there, with LIP_GAP clearance."""
    o = HALF - WALL - LIP_GAP
    i = o - LIP_W
    e = SCREW_XY - 4.5 - LIP_GAP          # stop short of the corner bosses
    z0, z1 = PLATE_T, PLATE_T + LIP_H
    lip = (bx(-e, e, -o, -i, z0, z1) + bx(-e, e, i, o, z0, z1)
           + bx(-o, -i, -e, e, z0, z1) + bx(i, o, -e, e, z0, z1))
    lip -= bx(-8.0, 8.0, i - 1, o + 1, z0 - 1, z1 + 1)  # rear: the USB-C plug passes over here
    # shell features inside the wall at lip height (the wall itself is left out)
    near = shell & bx(-(HALF - WALL - 0.01), HALF - WALL - 0.01, -(HALF - WALL - 0.01), HALF - WALL - 0.01,
                      z0 - 0.01, z1 + 0.5)
    # raised copies too, so the cut runs the full lip height above the 1 mm wall feet
    for dz in (0.0, 0.9, 1.8):
        for dx, dy in ((LIP_GAP, 0), (-LIP_GAP, 0), (0, LIP_GAP), (0, -LIP_GAP)):
            lip -= Pos(dx, dy, dz) * near
    keep = [s for s in lip.solids() if s.volume > 4 * LIP_W * LIP_H]  # drop slivers
    out = keep[0]
    for s in keep[1:]:
        out += s
    return out


def make_plate():
    plate = extrude(RectangleRounded(BASE, BASE, CORNER_R), amount=PLATE_T)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * SCREW_XY, sy * SCREW_XY
            plate -= Pos(x, y, CBORE_DEPTH / 2) * Cylinder(CBORE_D / 2, CBORE_DEPTH + 0.01)
            plate -= bridged_hole(x, y, CBORE_DEPTH, PLATE_T + 1, CBORE_D)
            plate -= Pos(sx * 28, sy * 28, 0.3) * Cylinder(4.5, 0.61)  # feet

    def u_cradle(x0, x1, half_y, top, slot):
        c = bx(x0, x1, -half_y, half_y, PLATE_T, top)
        c -= bx(x0 - 1, x1 + 1, -slot / 2, slot / 2, AXIS_Z, top + 1)
        return c - cyl_x(x0 - 1, x1 + 1, slot)

    plate += u_cradle(-3, 3, 9, CRADLE_TOP, 7.4)
    for s in (-1, 1):
        x = sorted((s * UPRIGHT[0], s * UPRIGHT[1]))
        plate += u_cradle(*x, 10, CRADLE_TOP, ENC_BUSH_D + 0.3)
        # encoder socket behind the upright: floor + two cheeks
        xs = sorted((s * UPRIGHT[1], s * (UPRIGHT[1] + ENC_BODY_L + 0.5)))
        xf = sorted((s * UPRIGHT[1], s * (UPRIGHT[1] + ENC_LEDGE)))
        w, h = ENC_BODY_W / 2, ENC_BODY_H / 2
        plate += bx(*xf, -w - 2.5, w + 2.5, PLATE_T, AXIS_Z - h)
        for sy in (-1, 1):
            ys = sorted((sy * w, sy * (w + 2.5)))
            plate += bx(*xs, *ys, PLATE_T, AXIS_Z + h - 1)

    # MCU seats: four corner posts, so the soldered long edges stay clear.
    # The board drops in from above and is held with a dab of hot glue.
    y0, y1 = HALF - WALL - MCU_L - 1.0, HALF - WALL - 1.0
    z0 = PLATE_T + 2.5
    plate += bx(-MCU_W / 2 - 0.3, MCU_W / 2 + 0.3, y0 - 2, y0 - 0.2, PLATE_T, z0 + 3)  # stop
    for s in (-1, 1):
        for ys in ((y0, y0 + 2), (y1 - 2, y1)):
            plate += bx(*sorted((s * (MCU_W / 2 - 2), s * (MCU_W / 2 + 0.3))), *ys, PLATE_T, z0)
            plate += bx(*sorted((s * (MCU_W / 2 + 0.3), s * (MCU_W / 2 + 1.8))), *ys, PLATE_T, z0 + MCU_T + 0.5)
    return plate


def d_bore(x0, x1, rib=None):
    """D-shaped bore along X with crush ribs reaching `rib` mm into the seated shaft
    (RIB_I by default; 0 for none). The lead-in for the ribs is the cone the bore is
    entered through (see make_wheel)."""
    rib = RIB_I if rib is None else rib
    r = ENC_SHAFT_D / 2 + FIT
    flat = ENC_SHAFT_FLAT - ENC_SHAFT_D / 2 + FIT
    c = cyl_x(x0, x1, 2 * r)
    keep = bx(x0 - 1, x1 + 1, -r - 1, r + 1, -r - 1, flat)
    bore = c & (Pos(0, 0, AXIS_Z) * Rot(CLOCK_OFFSET_DEG, 0, 0) * keep)
    if rib > 0:
        ribs = None
        for a in RIB_ANGLES:
            # with its flat seated on the bore's flat, the shaft sits FIT off-centre
            # towards the flat, so its surface is at this radius in direction a
            surface = ENC_SHAFT_D / 2 + FIT * cos(radians(a))
            one = Rot(a, 0, 0) * bx(x0 - 1, x1 + 1, -RIB_W / 2, RIB_W / 2, surface - rib, r + 0.3)
            ribs = one if ribs is None else ribs + one
        bore -= Pos(0, 0, AXIS_Z) * Rot(CLOCK_OFFSET_DEG, 0, 0) * ribs
    return bore


def _text(label):
    if Path(FONT_PATH).exists():
        return Text(label, font_size=TEXT_SIZE, font_path=FONT_PATH)
    return Text(label, font_size=TEXT_SIZE, font=FONT, font_style=FontStyle.BOLD)


def wheel_bore(inner_sign, rib=None):
    """Everything cut for the encoder in a wheel: the bushing pocket from the outer face,
    a 45 degree cone down to the D-flat, and the ribbed D bore."""
    xo = -inner_sign * WHEEL_OUT
    pocket_floor = MOUNT_X - ENC_SHAFT_L + ENC_FLAT_L - 0.5  # round part of the shaft stays clear of the D bore
    cut = cyl_x(-inner_sign * pocket_floor, xo + inner_sign * -1, ENC_BUSH_D + 1.5)
    # the cone keeps the pocket's roof printable (the wheel prints outer face down) and
    # is the lead-in for the crush ribs
    r0, r1 = (ENC_BUSH_D + 1.5) / 2, ENC_SHAFT_FLAT - ENC_SHAFT_D / 2 + FIT
    cut += Pos(-inner_sign * (pocket_floor - (r0 - r1) / 2), 0, AXIS_Z) * Rot(0, inner_sign * 90, 0) * Cone(r0, r1, r0 - r1)
    return cut + d_bore(*sorted((-inner_sign * BORE_END, -inner_sign * (pocket_floor + 0.5))), rib)


def make_wheel(inner_sign, labels):
    """inner_sign=+1: left wheel, inner face towards +X."""
    xo = -inner_sign * WHEEL_OUT
    xi = -inner_sign * WHEEL_IN
    span = sorted((xo, xi))
    w = cyl_x(*span, 2 * WHEEL_R)
    w = chamfer(w.edges().filter_by(lambda e: e.length > 100), 0.6)

    # ribbed grip bands - one rib per click
    for x0 in (span[0] - 0.01, span[1] - GRIP_W):
        sk = Sketch()
        for i in range(N_POS):
            phi = (i + 0.5) * PITCH
            y, z = -(WHEEL_R + 0.4) * sin(radians(phi)), (WHEEL_R + 0.4) * cos(radians(phi))
            sk += Pos(y, z) * Circle(GRIP_CUT_R)
        plane = Plane.YZ.offset(x0)
        cut = extrude(plane * sk, amount=GRIP_W + 0.01)
        w -= Pos(0, 0, AXIS_Z) * cut

    # stub boss that rests in the centre cradle
    w += cyl_x(xi, -inner_sign * 0.3, 7.0)

    w -= wheel_bore(inner_sign)

    # engraved numerals, labels[i] sits at phi = i * PITCH
    xc = (span[0] + span[1]) / 2
    for i, label in enumerate(labels):
        phi = radians(i * PITCH)
        n = (0, -sin(phi), cos(phi))
        o = (xc, n[1] * (WHEEL_R - TEXT_DEPTH), AXIS_Z + n[2] * (WHEEL_R - TEXT_DEPTH))
        txt = _text(label)
        w -= Plane(origin=o, x_dir=(1, 0, 0), z_dir=n) * extrude(txt, amount=2.0)
    return w


def spin(part, label_index):
    """Rotate a wheel about its axle so labels[label_index] is in the window."""
    return Pos(0, 0, AXIS_Z) * Rot(WINDOW_PHI - label_index * PITCH, 0, 0) * Pos(0, 0, -AXIS_Z) * part


def make_dummies():
    """Grey stand-ins for bought parts, for fit checks and renders only."""
    w, h = 7.0, 6.7
    out = {}
    for name, s in (("enc_l", -1), ("enc_r", 1)):
        xs = sorted((s * MOUNT_X, s * (MOUNT_X + ENC_BODY_L)))
        xb = sorted((s * MOUNT_X, s * (MOUNT_X - ENC_BUSH_L)))
        xp = sorted((s * (MOUNT_X + ENC_BODY_L), s * (MOUNT_X + ENC_BODY_L + ENC_PIN_L)))
        e = bx(*xs, -6.25, 6.25, AXIS_Z - h, AXIS_Z + h) + cyl_x(*xb, ENC_BUSH_D)
        e += bx(*sorted((s * (MOUNT_X + 2), s * (MOUNT_X + 3.5))), -w, w, AXIS_Z - 1, AXIS_Z + 1)  # side tabs
        for y in (-2.5, 0, 2.5):
            e += bx(*xp, y - 0.4, y + 0.4, AXIS_Z - 7.9, AXIS_Z - 7.1)
            e += bx(*sorted((s * (MOUNT_X + 4.8), s * (MOUNT_X + ENC_BODY_L))), y - 0.4, y + 0.4, AXIS_Z - 7.9, AXIS_Z - 6.7)
        out[name] = e
    y0, y1 = HALF - WALL - MCU_L - 1.0, HALF - WALL - 1.0
    z0 = PLATE_T + 2.5
    out["mcu"] = bx(-MCU_W / 2, MCU_W / 2, y0, y1, z0, z0 + MCU_T) + bx(-4.5, 4.5, y1 - 7, y1 + 0.8, z0 + MCU_T, z0 + MCU_T + 3.2)
    wi = HALF - WALL
    sw = bx(wi - 5, wi, SW_Y - 5.55, SW_Y + 5.55, SW_Z - 2.9, SW_Z + 2.9)     # body
    sw += bx(wi - 0.6, wi, SW_Y - 9.5, SW_Y + 9.5, SW_Z - 2.9, SW_Z + 2.9)    # mounting ears
    for y in (-3, 0, 3):
        sw += bx(wi - 8.5, wi - 5, SW_Y + y - 0.4, SW_Y + y + 0.4, SW_Z - 0.2, SW_Z + 0.2)  # pins
    out["switch"] = sw + switch_actuator(0.0)
    head_top = CBORE_DEPTH
    screws = None
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = Pos(sx * SCREW_XY, sy * SCREW_XY, 0)
            one = p * Pos(0, 0, head_top - SCREW_HEAD_H / 2) * Cylinder(SCREW_HEAD_D / 2, SCREW_HEAD_H)
            one += p * Pos(0, 0, head_top + SCREW_L / 2) * Cylinder(1.5, SCREW_L)
            screws = one if screws is None else screws + one
    out["screws"] = screws
    out["nuts"] = nut_set(0.0)
    leds = None
    for s in (-1, 1):
        xc = s * (WHEEL_IN + WHEEL_OUT) / 2
        one = led_cyl(xc, LED_D, -LED_LEN, 0) + led_cyl(xc, LED_D + 0.8, -LED_LEN - 1, -LED_LEN)
        for dx in (-1.27, 1.27):
            one += led_cyl(xc + dx, 0.5, -LED_LEN - 5, -LED_LEN - 1)  # leads, before bending
        leds = one if leds is None else leds + one
    out["leds"] = leds
    return out


def nut_set(inboard):
    """The four nuts, each slid `inboard` mm back along its slot."""
    nuts = None
    for sx in (-1, 1):
        for sy in (-1, 1):
            one = Pos(sx * (SCREW_XY - inboard), sy * SCREW_XY, NUT_Z + 0.02) * nut_hex(NUT_AF, NUT_H - 0.04)
            nuts = one if nuts is None else nuts + one
    return nuts


def switch_actuator(offset):
    """EG1201A slider: 3 mm wide, 5.5 mm tall, travels +/-1.5 mm along Y."""
    wi = HALF - WALL
    y = SW_Y + offset
    return bx(wi, wi + 5.5, y - 1.5, y + 1.5, SW_Z - 1.5, SW_Z + 1.5)


def build():
    shell = make_shell()
    return {
        "plate": make_plate() + plate_lip(shell),
        "shell": shell,
        "wheel_hours": make_wheel(+1, HOURS),
        "wheel_minutes": make_wheel(-1, MINUTES),
    }


def print_pose(name, part):
    """Orient each part as it should go on the bed, z-min = 0."""
    if name == "wheel_hours":
        part = Rot(0, -90, 0) * part
    elif name == "wheel_minutes":
        part = Rot(0, 90, 0) * part
    b = part.bounding_box()
    return Pos(-b.center().X, -b.center().Y, -b.min.Z) * part


def main():
    root = Path(__file__).parent
    (root / "stl").mkdir(exist_ok=True)
    (root / "step").mkdir(exist_ok=True)
    parts = build()
    for name, part in parts.items():
        print(f"{name:14s} valid={part.is_valid} vol={part.volume / 1000:6.1f} cm3 "
              f"bbox={tuple(round(v, 1) for v in part.bounding_box().size)}")
        export_stl(print_pose(name, part), str(root / "stl" / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.15)
        export_step(part, str(root / "step" / f"{name}.step"))
    return parts


if __name__ == "__main__":
    main()
