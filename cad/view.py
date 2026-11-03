"""Interactive 3D viewer for the assembled HueWheel (needs pyvista).

    conda run -n base python cad/assemble.py   # once, and after any CAD change
    python cad/view.py

Mouse: left-drag rotates, right-drag or scroll zooms, middle-drag (or shift+left) pans.
Checkboxes on the left show or hide groups of parts. The sliders explode the assembly and move
a section cut. Keys: n changes the cut axis (X, Y, Z), r resets the camera, q quits.

The wheels show 07:30, as posed by assemble.py.
"""
import sys

import numpy as np
import pyvista as pv

from scene import COL, EXPLODE, load_meshes

GROUPS = {  # checkbox label: parts
    "Shell": ["shell"],
    "Base plate": ["plate"],
    "Wheels": ["wheel_hours", "wheel_minutes"],
    "Encoders": ["enc_l", "enc_r"],
    "Electronics": ["mcu", "switch", "leds"],
    "Screws + nuts": ["screws", "nuts"],
}
AXES = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}


class Viewer:
    def __init__(self, off_screen=False):
        self.base = load_meshes()
        self.shown = {n: True for n in self.base}
        self.explode = 0.0
        self.cut_on = False
        self.cut_axis = "X"
        self.cut_pos = 0.5           # 0..1 across the assembly in the cut axis
        self.bounds = np.array(pv.merge(list(self.base.values())).bounds).reshape(3, 2)

        p = self.p = pv.Plotter(window_size=(1400, 950), off_screen=off_screen,
                                title="HueWheel viewer")
        p.set_background("#f4f3ef", top="#d8dde3")
        self.disp, self.actors = {}, {}
        for n, m in self.base.items():
            self.disp[n] = m.copy()
            self.actors[n] = p.add_mesh(self.disp[n], color=COL[n], smooth_shading=False,
                                        split_sharp_edges=True, specular=0.2, feature_angle=30)

        for i, (label, parts) in enumerate(GROUPS.items()):
            y = 880 - i * 45
            p.add_checkbox_button_widget(lambda on, parts=parts: self.set_group(parts, on),
                                         value=True, position=(12, y), size=32, color_on="#4a7bd1")
            p.add_text(label, position=(54, y + 6), font_size=11, color="#222222")
        y = 880 - len(GROUPS) * 45 - 20
        p.add_checkbox_button_widget(self.set_cut, value=False, position=(12, y), size=32,
                                     color_on="#c23b3b")
        p.add_text("Section cut", position=(54, y + 6), font_size=11, color="#222222")

        p.add_slider_widget(self.set_explode, (0.0, 1.0), value=0.0, title="Explode",
                            pointa=(0.30, 0.07), pointb=(0.55, 0.07), style="modern",
                            interaction_event="always")
        self.cut_slider = p.add_slider_widget(self.set_cut_pos, (0.0, 1.0), value=self.cut_pos,
                                              title=self.cut_title(), pointa=(0.65, 0.07),
                                              pointb=(0.90, 0.07), style="modern",
                                              interaction_event="end")
        p.add_text("Drag: rotate   Scroll: zoom   Shift-drag: pan\n"
                   "n: cut axis   r: reset view   q: quit",
                   position="upper_right", font_size=9, color="#555555")
        p.add_key_event("n", self.next_axis)
        p.add_axes()
        p.camera_position = [(140, -230, 160), (0, 0, 24), (0, 0, 1)]  # front right: looks into the cut

    # --- callbacks ---------------------------------------------------------------
    def set_group(self, parts, on):
        for n in parts:
            self.shown[n] = on
        self.update()

    def set_explode(self, v):
        self.explode = v
        self.update()

    def set_cut(self, on):
        self.cut_on = on
        self.update()

    def set_cut_pos(self, v):
        self.cut_pos = v
        if hasattr(self, "cut_slider"):  # the slider calls this once while being created
            self.cut_slider.GetRepresentation().SetTitleText(self.cut_title())
        if self.cut_on:
            self.update()

    def next_axis(self):
        keys = list(AXES)
        self.cut_axis = keys[(keys.index(self.cut_axis) + 1) % len(keys)]
        self.cut_slider.GetRepresentation().SetTitleText(self.cut_title())
        self.update()

    # --- drawing -----------------------------------------------------------------
    def cut_value(self):
        lo, hi = self.bounds["XYZ".index(self.cut_axis)]
        return lo + self.cut_pos * (hi - lo)

    def cut_title(self):
        return f"Section {self.cut_axis} = {self.cut_value():.1f} mm"

    def update(self):
        normal = AXES[self.cut_axis]
        origin = [0.0, 0.0, 0.0]
        origin["XYZ".index(self.cut_axis)] = self.cut_value()
        for n, base in self.base.items():
            actor = self.actors[n]
            actor.SetVisibility(self.shown[n])
            if not self.shown[n]:
                continue
            m = base.translate(np.array(EXPLODE[n]) * self.explode, inplace=False)
            if self.cut_on:
                m = self.clip(m, normal, origin)
            self.disp[n].copy_from(m)
        self.p.render()

    @staticmethod
    def clip(m, normal, origin):
        """Cut away the +normal side; cap the cut face so parts read as solid."""
        try:
            out = m.clip_closed_surface(normal=[-c for c in normal], origin=origin)
            if out.n_points:
                return out
        except Exception:
            pass
        out = m.clip(normal=normal, origin=origin)
        return out if isinstance(out, pv.PolyData) else out.extract_surface(algorithm="dataset_surface")


if __name__ == "__main__":
    if "--screenshot" in sys.argv:  # non-interactive smoke test: python cad/view.py --screenshot out.png
        v = Viewer(off_screen=True)
        v.set_explode(0.4)
        v.set_cut(True)
        v.p.screenshot(sys.argv[sys.argv.index("--screenshot") + 1])
    else:
        Viewer().p.show()
