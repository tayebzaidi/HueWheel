"""Render docs/renders/*.png from cad/build/*.stl (needs pyvista + a display
or xvfb-run):  xvfb-run -a python cad/render.py"""
from pathlib import Path

import numpy as np
import pyvista as pv

ROOT = Path(__file__).parent
OUT = ROOT.parent / "docs" / "renders"
COL = {"plate": "#3c4148", "shell": "#d9d5cc", "wheel_hours": "#e0803a",
       "wheel_minutes": "#e0803a", "enc_l": "#8d939b", "enc_r": "#8d939b", "mcu": "#2f6d4f"}
EXPLODE = {"plate": (0, 0, 0), "shell": (0, 0, 90), "wheel_hours": (-8, 0, 34),
           "wheel_minutes": (8, 0, 34), "enc_l": (-62, 0, 34), "enc_r": (62, 0, 34), "mcu": (0, 42, 0)}
meshes = {n: pv.read(ROOT / "build" / f"{n}.stl") for n in COL}


def shot(name, parts, cam, offs=None, clip=None, size=(1400, 1050), zoom=1.0):
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background("white")
    for n in parts:
        m = meshes[n].copy()
        if offs:
            m = m.translate(offs[n])
        if clip:
            m = m.clip(normal=clip[0], origin=clip[1], invert=True)
            if m.n_points == 0:
                continue
        p.add_mesh(m, color=COL[n], smooth_shading=False, split_sharp_edges=True,
                   specular=0.15, feature_angle=30)
    p.enable_anti_aliasing("ssaa")
    p.camera_position = cam
    p.camera.zoom(zoom)
    p.screenshot(OUT / f"{name}.png")
    p.close()


def view(az, el, dist, focus=(0, 0, 28)):
    a, e = np.radians(az), np.radians(el)
    pos = (focus[0] + dist * np.sin(a) * np.cos(e), focus[1] - dist * np.cos(a) * np.cos(e),
           focus[2] + dist * np.sin(e))
    return [pos, focus, (0, 0, 1)]


OUT.mkdir(parents=True, exist_ok=True)
ALL = list(COL)
shot("assembled_front", ALL, view(-28, 34, 190))
shot("assembled_rear", ALL, view(150, 30, 190))
shot("window_closeup", ALL, view(0, 46, 100, (0, -14, 46)), size=(1400, 800))
shot("exploded", ALL, view(-30, 16, 420, (0, 0, 80)), offs=EXPLODE, size=(1200, 1200))
shot("internals", [n for n in ALL if n != "shell"], view(-30, 38, 165))
shot("section_x10", ALL, view(90, 0, 150), clip=((1, 0, 0), (10.5, 0, 0)))
shot("section_y0", ALL, view(0, 0, 150), clip=((0, -1, 0), (0, 0, 0)))
