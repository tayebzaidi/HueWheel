"""Shared by render.py and view.py: part colours, exploded-view offsets, mesh loading."""
from pathlib import Path

import pyvista as pv

ROOT = Path(__file__).parent
BUILD = ROOT / "build"
COL = {"plate": "#3c4148", "shell": "#d9d5cc", "wheel_hours": "#e0803a",
       "wheel_minutes": "#e0803a", "enc_l": "#8d939b", "enc_r": "#8d939b", "mcu": "#2f6d4f",
       "switch": "#c23b3b", "screws": "#c9ccd1", "inserts": "#e8c547", "leds": "#f2f2f2"}
EXPLODE = {"plate": (0, 0, 0), "shell": (0, 0, 90), "wheel_hours": (-8, 0, 34),
           "wheel_minutes": (8, 0, 34), "enc_l": (-62, 0, 34), "enc_r": (62, 0, 34), "mcu": (0, 42, 0),
           "switch": (48, 0, 90), "screws": (0, 0, -35), "inserts": (0, 0, 90), "leds": (0, 0, 90)}


def load_meshes():
    """Assembly-pose meshes written by assemble.py."""
    missing = [n for n in COL if not (BUILD / f"{n}.stl").exists()]
    if missing:
        raise SystemExit(f"cad/build is missing {', '.join(missing)}. "
                         "Run first:  conda run -n base python cad/assemble.py")
    return {n: pv.read(BUILD / f"{n}.stl") for n in COL}
