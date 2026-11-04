"""Render docs/renders/*.png from cad/build/*.stl (needs pyvista + a display
or xvfb-run):  xvfb-run -a python cad/render.py"""
import numpy as np
import pyvista as pv

from scene import COL, EXPLODE, ROOT, load_meshes

OUT = ROOT.parent / "docs" / "renders"
meshes = load_meshes()


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
shot("assembled_front", ALL, view(-28, 34, 240, (0, 0, 24)))
shot("assembled_rear", ALL, view(150, 30, 240, (0, 0, 24)))
shot("window_closeup", ALL, view(0, 46, 100, (0, -14, 46)), size=(1400, 800))
shot("exploded", ALL, view(-30, 16, 500, (0, 0, 62)), offs=EXPLODE, size=(1200, 1200))
shot("internals", [n for n in ALL if n != "shell"], view(-30, 38, 200, (0, 0, 24)))
shot("encoder_cradle", ["plate", "enc_r", "wheel_minutes"], view(55, 25, 90, (28, 0, 28)), size=(1200, 900))
shot("underside", ALL, view(-30, -40, 240, (0, 0, 22)))
shot("mcu_bay", ["plate", "mcu", "enc_r", "enc_l"], view(160, 38, 95, (0, 28, 8)), size=(1200, 900))
shot("section_x0_usb", ALL, view(90, 0, 150), clip=((1, 0, 0), (0, 0, 0)))
shot("section_switch", ALL, view(0, 0, 90, (30, 0, 22)), clip=((0, -1, 0), (0, -15, 0)), size=(1200, 900))
shot("section_insert", ["plate", "shell", "screws", "inserts"], view(0, 0, 70, (32, 0, 12)), clip=((0, -1, 0), (0, 36, 0)), size=(1200, 900))
shot("plate_lip", ["plate"], view(-30, 40, 200, (0, 0, 6)))
for el in (10, 25, 46):
    shot(f"eye_level_{el}deg", ALL, view(0, el, 300, (0, -16, 46)), size=(1100, 520), zoom=2.6)
shot("section_led", ALL, view(90, 0, 110, (10.5, -14, 36)), clip=((1, 0, 0), (10.5, 0, 0)), size=(1200, 900))
shot("section_x10", ALL, view(90, 0, 150), clip=((1, 0, 0), (10.5, 0, 0)))
shot("section_y0", ALL, view(0, 0, 150), clip=((0, -1, 0), (0, 0, 0)))
# printability: what the shell looks like from the bed side, and the new bridges
shot("shell_inside", ["shell"], view(-25, -60, 200, (0, 0, 20)))
shot("section_x19_caps", ALL, view(90, 0, 150), clip=((1, 0, 0), (19.5, 0, 0)))
shot("section_x24_encoder_cap", ALL, view(90, 0, 150), clip=((1, 0, 0), (24.0, 0, 0)))
shot("counterbore", ["plate"], view(-20, -60, 40, (36, -36, 2)), size=(1200, 900))


def led_insert():
    """Shell upside down, as it is held to fit the LEDs: each LED drops in through the
    open bottom (ghosts), moves across to the slope, then slides up into its slot."""
    import huewheel as hw
    tip, u = hw.led_axis()
    n = np.array((0, u[1], -u[0]))
    mid = np.array((10.5, tip[0] - hw.LED_LEN / 2 * u[0], tip[1] - hw.LED_LEN / 2 * u[1]))
    clip = ((1, 0, 0), (10.5, 0, 0))
    p = pv.Plotter(off_screen=True, window_size=(1200, 900))
    p.set_background("white")
    p.add_mesh(meshes["shell"].clip(normal=clip[0], origin=clip[1], invert=True), color=COL["shell"],
               smooth_shading=False, split_sharp_edges=True, specular=0.15)
    led = meshes["leds"].clip(normal=clip[0], origin=(0, 0, 0), invert=False)  # the right-hand LED only
    steps = [(np.zeros(3), 1.0), (12 * n, 0.45), (12 * n + (0, 0, -14), 0.3), (12 * n + (0, 0, -28), 0.2)]
    for off, alpha in steps:
        p.add_mesh(led.translate(off), color="#e8c547" if alpha < 1 else "#c23b3b", opacity=alpha)
    pts = np.array([s[0] for s in steps][::-1]) + mid
    p.add_mesh(pv.Spline(pts, 60).tube(radius=0.35), color="#2f6d4f")
    p.enable_anti_aliasing("ssaa")
    p.camera_position = [(110, -14, 14), (10.5, -14, 14), (0, 0, -1)]
    p.screenshot(OUT / "led_insert.png")
    p.close()


led_insert()
