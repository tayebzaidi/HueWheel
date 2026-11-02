# HueWheel

A small bedside controller for setting a Philips Hue light alarm by feel: two notched
wheels, rolled like a mouse scroll wheel, set the wake-up time. The time reads
mechanically through a window, like a combination lock, so there is no screen.

![Assembled](docs/renders/assembled_front.png)

| Exploded | Cutaway |
|---|---|
| ![Exploded](docs/renders/exploded.png) | ![Section](docs/renders/section_x10.png) |

**Status:** first-pass CAD and BOM. Nothing has been printed or test-fitted, and there is
no firmware yet.

## How it works

- **Left wheel = hours** (00-23, 1 click = 1 hour). **Right wheel = minutes** (5-minute
  clicks; 00-55 appears twice around the wheel).
- Roll a wheel away from you to go later.
- The clicks come from the encoders. The rim ribs match them one-to-one, so each rib is one click.
- A slide switch on the right side turns the alarm on or off.
- A Seeed XIAO ESP32C3 sends the time to the Hue Bridge over Wi-Fi once the wheels stop moving.

## Dimensions

84 x 84 mm footprint, 52.6 mm tall. Wheels are 44 mm diameter, 14 mm wide, and stand 3 mm
proud of the deck. All key dimensions are parameters at the top of
[`cad/huewheel.py`](cad/huewheel.py).

## Parts

The full list, with a Have? column that updates the total, is in
[`bom/HueWheel_BOM.xlsx`](bom/HueWheel_BOM.xlsx). With the hardware already on hand, about **$18.70** is left to buy
(estimated prices, including $7 shipping). A USB charger and data cable are also needed; they are on hold in the BOM at about $6.
Everything comes from one DigiKey order.

Print settings and slicer estimates are on the workbook's Printed Parts tab: about 119 g and
10 hours on the default PrusaSlicer profile. The shell needs supports from the build plate.

## Assembly

1. Slide the XIAO into the plate rails from the rear, USB port facing out. Keep solder
   joints low on the board edges, because the rails grip there.
   Stick its antenna inside the rear wall, away from the wires.
2. Wire the encoders and slide switch (pin map to be defined with the firmware).
3. Press each wheel onto its encoder shaft.
4. Lower each wheel + encoder pair into the cradles: the bushing goes in the outer U-slot,
   the stub boss in the centre one, and the encoder body in its socket.
5. Fit the shell. Internal ribs stop the wheels and encoders lifting out.
6. Fasten from below with four M3 x 8 button head screws, then add the feet.

## Known risks to check on first print

- **Print one wheel first.** Encoder dimensions come from the Bourns datasheet, but the fit
  on a real part is untested. A 24-detent encoder is required as modelled.
- **Click strength.** The rated detent torque is low (30-90 gf-cm), which is only about
  14-41 gf at the rim of a 44 mm wheel. If the clicks feel faint, add a printed spring that
  rides in the existing rim ribs.
- **Numeral alignment.** The angle between the D-flat and the detents is unknown, so numbers
  may sit off-centre at a click. Measure it, then set `CLOCK_OFFSET_DEG` and reprint the wheels.
- **Wheel position is relative.** Encoders don't report absolute position. The firmware will
  save the position and needs a re-sync gesture for when a wheel is turned while unpowered.
  Changing the alarm in the Hue app won't move the wheels.
- **Hue wake-up API.** The plan is to edit the app's existing Wake Up automation. It is stored
  as a `behavior_instance` resource, whose schema is not publicly documented, so this needs
  testing against a real bridge. The fallback is a separate schedule owned by this device.

## Rebuilding the CAD

```bash
conda run -n base python cad/huewheel.py    # parts: cad/stl (print-ready), cad/step (untracked)
conda run -n base python cad/assemble.py    # interference check + cad/step/assembly.step
xvfb-run -a python cad/render.py            # docs/renders; needs pyvista, not in conda base
```
