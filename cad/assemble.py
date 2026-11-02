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
        if {na, nb} <= {"enc_l", "enc_r", "mcu", "switch", "screws"}:
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

    # assembly paths, largest clash along each path
    pairs = {"wheel+encoder drop-in": (["wheel_hours", "wheel_minutes", "enc_l", "enc_r"], ["plate", "mcu"]),
             "shell drop-on": (["shell", "switch"], ["plate", "mcu", "enc_l", "enc_r", "wheel_hours", "wheel_minutes"])}
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
