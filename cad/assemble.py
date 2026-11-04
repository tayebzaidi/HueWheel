"""Fit check + assembly export.  conda run -n base python cad/assemble.py

Shows the alarm set to 07:30.  Writes cad/step/assembly.step and per-part
assembly-pose STLs to cad/build/ (consumed by render.py).
"""
from itertools import combinations
from pathlib import Path

from build123d import Compound, Pos, export_step, export_stl

import huewheel as hw


def overlap(a, b):
    r = a & b
    if r is None:
        return 0.0
    return sum(s.volume for s in r.solids()) if hasattr(r, "solids") else r.volume


def main():
    root = Path(__file__).parent
    build = root / "build"
    build.mkdir(exist_ok=True)
    parts = hw.main()
    parts["wheel_hours"] = hw.spin(parts["wheel_hours"], 7)            # "07"
    parts["wheel_minutes"] = hw.spin(parts["wheel_minutes"], 6)        # "30"
    parts.update(hw.make_dummies())

    bad = 0
    for (na, a), (nb, b) in combinations(parts.items(), 2):
        if {na, nb} <= {"enc_l", "enc_r", "mcu", "switch", "screws", "inserts", "leds"}:
            continue
        v = overlap(a, b)
        if v > 0.01:
            bad += 1
            print(f"INTERFERENCE {na} / {nb}: {v:.2f} mm3")
    print("interference pairs:", bad)

    # the switch slider must clear the slot through its whole travel
    for off in (-1.5, 1.5):
        v = overlap(hw.switch_actuator(off), parts["shell"])
        print(f"switch slider at {off:+.1f} mm vs shell: {v:.2f} mm3")
        bad += v > 0.01

    # the screw must reach well into the insert without bottoming out in its hole
    screw_top = hw.CBORE_DEPTH + hw.SCREW_L
    grip = min(screw_top, hw.PLATE_T + hw.INSERT_L) - hw.PLATE_T
    room = hw.PLATE_T + hw.INSERT_HOLE_L - screw_top
    print(f"screw grips {grip:.1f} of {hw.INSERT_L:.1f} mm of insert thread, tip {room:.1f} mm short of the hole end")
    bad += grip < 4.0 or room < 0.3

    # each LED drops into its slot from inside the shell: straight out from the slope
    # wall, then down through the open bottom. Pushed further up the slot, it must stop.
    _, u = hw.led_axis()
    n = (u[1], -u[0])
    path = [Pos(0, k * n[0], k * n[1]) for k in (0.5, 1, 2, 3, 4, 6, 8, 10, 12)]
    path += [Pos(0, 0, -dz) * Pos(0, 12 * n[0], 12 * n[1]) for dz in (2, 4, 8, 12, 16, 24, 32, 40)]
    worst = max(overlap(p * parts["leds"], parts["shell"]) for p in path)
    stop = overlap(Pos(0, 0.5 * u[0], 0.5 * u[1]) * parts["leds"], parts["shell"])
    print(f"LED insertion: worst clash {worst:.2f} mm3; pushed 0.5 mm past its seat: {stop:.2f} mm3 (must be > 0)")
    bad += worst > 0.01 or stop < 0.01

    # assembly paths, largest clash along each path
    pairs = {"wheel+encoder drop-in": (["wheel_hours", "wheel_minutes", "enc_l", "enc_r"], ["plate", "mcu"]),
             "shell drop-on": (["shell", "switch", "inserts", "leds"], ["plate", "mcu", "enc_l", "enc_r", "wheel_hours", "wheel_minutes"])}
    for label, (moving, fixed) in pairs.items():
        worst = 0.0
        for dz in (1, 2, 4, 8, 12, 16, 24, 32, 45, 60):
            for m in moving:
                for f in fixed:
                    worst = max(worst, overlap(Pos(0, 0, dz) * parts[m], parts[f]))
        print(f"{label}: worst clash {worst:.2f} mm3")
        bad += worst > 0.01
    print("FIT CHECK", "FAILED" if bad else "PASSED")

    for name, p in parts.items():
        export_stl(p, str(build / f"{name}.stl"), tolerance=0.05, angular_tolerance=0.2)
    export_step(Compound(label="HueWheel", children=list(parts.values())),
                str(root / "step" / "assembly.step"))


if __name__ == "__main__":
    main()
