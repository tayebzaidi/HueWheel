# HueWheel

A small bedside controller for setting a Philips Hue wake-up light by feel. Roll two notched
wheels, like a mouse scroll wheel, and the time reads through a window like a combination
lock. There's no screen and no app to open, and a switch on the side turns the alarm on or off.

![Assembled](docs/renders/assembled_front.png)

| Exploded | Cutaway |
|---|---|
| ![Exploded](docs/renders/exploded.png) | ![Section](docs/renders/section_x10.png) |

> **Project status:** this is an untested first build. The wheels have been printed. The shell
> and plate were redesigned after the first print to need no supports, and that version hasn't
> been printed yet. The firmware hasn't run on a real board. Changing a real alarm has only
> been tried from a PC, on a BSB002 bridge. Expect to adjust things along the way: [what might need adjusting](#what-might-need-adjusting).

## Using it

- **Left wheel: hours.** Runs 00-23, one hour per click.
- **Right wheel: minutes.** Moves in 5-minute clicks. 00-55 appears twice around the wheel.
- **Roll a wheel away from you** to go later.
- **Slide switch on the right:** alarm on or off.

Stop touching it, and about 2.5 seconds later the new time goes to your Hue Bridge. The windows
light up for 5 seconds after each click, so you can read them in the dark.

**A short blink every 5 seconds means the bridge doesn't have your latest time yet**, usually
because Wi-Fi is down. It keeps retrying, but don't rely on the alarm until the blinking stops.

Good to know:

- It changes the time and on/off only. The days, rooms and fade stay as you set them in the
  Hue app, so an alarm set to weekdays won't ring on a Saturday.
- The wheels can't move themselves. If you change the alarm in the Hue app, the wheels will
  show the old time until you next roll one, and then the wheels' time wins.
- It needs USB power all the time. It keeps its position through a power cut, as long as
  nobody turns a wheel while it's unplugged.

## Building one

You'll need a 3D printer, a soldering iron, a hot glue gun, and a Linux PC for flashing the
firmware. The commands here are for Linux, and they start from the top folder of this repo
unless a step says otherwise.

### 1. Get the parts

The full list is in [`bom/HueWheel_BOM.xlsx`](bom/HueWheel_BOM.xlsx). Fill in its Have? column
and the total updates. From scratch you need:

- A Philips Hue Bridge with at least one Wake Up automation set up in the Hue app
- 2 Bourns PEC11R-4215F-N0024 rotary encoders. **It must be a 24-detent model**, because the
  wheel numbering depends on it.
- 1 Seeed XIAO ESP32C3, the version without pre-soldered headers
- 1 E-Switch EG1201A slide switch
- 2 LEDs, 5 mm, red or amber. For 3 mm LEDs, set `LED_D = 3.0` and `LED_LEN = 5.3` in
  `cad/huewheel.py` and re-export.
- 2 resistors, 220-470 ohm
- 4 M3 x 8 button head screws and 4 M3 nuts
- Hookup wire, about 1 m in total
- A USB charger, and a USB-A to USB-C cable that carries data
- About 120 g of PLA

The electronics come from one DigiKey order. With the small parts already on hand, that's
about $18.70 including an estimated $7 shipping, plus about $6 for the charger and cable if
you need them. These are estimates, so check them at checkout.

### 2. Print the parts

**Print the rib test piece first:** [`cad/test/rib_test.stl`](cad/test/rib_test.stl), at
0.12 mm like the wheels, as exported. Each wheel grips its encoder shaft with three small crush
ribs in the D-shaped bore, which the shaft squashes as the wheel goes on. The test piece has
three hubs with ribs reaching 0.1, 0.2 and 0.3 mm into the shaft, each cut exactly like a
wheel's bore. Push an encoder shaft into each hub from the bottom, flat first, then pull it out.
Choose the tightest one that goes fully on by hand without cracking and has no wobble or
turning play. Set `RIB_I` in `cad/huewheel.py` to that size and re-export. The test piece is not
part of the build.

Two more test pieces, both at 0.2 mm layers as exported. Neither is part of the build:

- [`cad/test/nut_test.stl`](cad/test/nut_test.stl): three copies of the shell's captive-nut
  boss, all with 2.6 mm high slots. The slot is 0.0, 0.1 or 0.2 mm wider than the nut across
  the flats, engraved on the back. Pick the tightest one the nut slides into and stays in, and
  set `NUT_FIT` and `NUT_SLOT_H` to match.
- [`cad/test/clamp_test.stl`](cad/test/clamp_test.stl): three copies of the plate's encoder
  socket, with uprights 1.5, 2.0 and 2.5 mm thick (the plate uses 3.0). Seat an encoder in
  each, put its own washer and nut on the bushing, and tighten. This shows how thin the upright
  must be for the nut to clamp it, and checks the socket fit.

Then print one wheel and try it on an encoder before printing the rest from
[`cad/stl`](cad/stl):

| Part | File | Layer height | Bambu Studio profile |
|---|---|---|---|
| Shell | `shell.stl` | 0.2 mm, first layer 0.2 mm too | 0.20mm Standard |
| Base plate | `plate.stl` | 0.2 mm, first layer 0.2 mm too | 0.20mm Standard |
| Hours wheel | `wheel_hours.stl` | 0.12 mm | 0.12mm Fine |
| Minutes wheel | `wheel_minutes.stl` | 0.12 mm | 0.12mm Fine |

These settings were worked out on a Bambu Lab X1 Carbon with PLA. Any printer that bridges
reasonably well should work.

**All parts:**

- **Turn supports off, including automatic supports.** No part needs them, and on the wheels
  they would fill the engraved numerals. Everything that hangs is either a bridge between two
  walls or a slope of 45 degrees or steeper.
- **Don't rotate or flip anything.** The files are already in print orientation: the shell open
  side down, the plate bottom face down, and the wheels outer face down.
- 15% infill and the default walls are fine. Expect about 145 g of filament in total.
- No brim is needed. Every tall feature inside the shell is joined to the outer walls, and the
  thin inner walls have a 1 mm tall foot that widens them on the first layers.
- Slicers use one layer height for everything on a plate, so print the wheels on a separate
  plate from the shell and base plate.

**Shell and base plate:**

- **The 0.2 mm layers matter.** Each screw hole and nut slot starts with two 0.2 mm bridge
  layers, a slot and then a square opening, and they are drawn to land on 0.2 mm layer lines.
  A thicker first layer or adaptive layer height shifts them off those lines.
- **Turn off thick bridges** ("Thick bridges" in Bambu Studio's Quality settings). Thick bridges
  are laid at about nozzle height, which merges the two thin layers into one.
- Print the shell first, because it has the most bridges. The longest is the 24 mm roof of the
  tunnel over the microcontroller board. The flat undersides over the wheels and encoders are
  up to about 21 mm long.

**Wheels:** slow outer walls, high part cooling, and the seam placed in a rib groove.

**Check after printing:**

- **The flat undersides over the encoders** should be flat. They clear the encoder bodies by
  0.5 mm and the cradle tops by 0.2 mm, so sand or trim any droop.
- **The square opening above each screw hole and nut slot** should be clear. Pick out any
  strings, but don't drill the layers out, because the screw passes through the square.
- **Each M3 nut** should slide all the way into its slot. The slot is 2.4 mm tall, the same as
  the nut, so a snug push is expected. If one won't go, file the slot roof lightly.
- **The low lip around the edge of the plate** should let the shell drop on without forcing.
- **Each LED slot** inside the front slope should be clear between its two walls, with a small
  step near the top where the slot narrows.
- **The doorway at the bottom of each rear encoder wall** should be open. The encoder and switch
  wires pass through it to the board.

Darken the engraved numerals with a fine marker or paint pen. Use black or another dark
colour, because a red numeral disappears under a red LED.

### 3. Wire the electronics

Solder everything together **before** gluing anything into the shell, leaving enough wire to
reach each part's final position.

| From | To XIAO pin |
|---|---|
| Hours encoder (left), pin A | D1 |
| Hours encoder (left), pin B | D2 |
| Minutes encoder (right), pin A | D3 |
| Minutes encoder (right), pin B | D4 |
| Both encoders, centre pin C | GND |
| Slide switch, centre lug | D5 |
| Slide switch, one outer lug | GND |
| Each LED long leg, through its own resistor | D10 |
| Each LED short leg | GND |

Leave the other switch lug unconnected, and leave D0, D8 and D9 free, because they can stop the
board booting. Cover the resistor joints with tape or heat shrink. Connect the included
antenna to the XIAO.

### 4. Pair with your Hue Bridge

The Python tool below needs no extra packages. It stores everything in
`firmware/include/secrets.h`, which git ignores.

1. Find the bridge:
   ```bash
   python3 tools/hue_dryrun.py discover
   ```
2. Press the round button on top of the bridge, then within 30 seconds run:
   ```bash
   python3 tools/hue_dryrun.py pair
   ```
3. List your Wake Up automations and find the one the wheels should control. Each one shows
   its name under `metadata` and its `id` at the top:
   ```bash
   python3 tools/hue_dryrun.py list
   ```
4. Choose it, using that `id`:
   ```bash
   python3 tools/hue_dryrun.py use <id>
   ```
   While you're testing, pick a spare automation that's switched off, so your real alarm stays
   safe. You can run this again and re-upload when the device is ready for real use.
5. Open `firmware/include/secrets.h` and fill in `WIFI_SSID` and `WIFI_PASSWORD`. The network
   must be **2.4 GHz**, because this board has no 5 GHz radio.

Then give the bridge a fixed address in your router (a "DHCP reservation"). The device doesn't
search for the bridge, so it loses contact if that address changes.

You can also try a change from your PC first. `plan` only shows what would be sent, `apply`
really sends it, and `restore` undoes it:

```bash
python3 tools/hue_dryrun.py plan 07:30 on
python3 tools/hue_dryrun.py apply 07:30 on
python3 tools/hue_dryrun.py restore
```

### 5. Upload the firmware

1. Install PlatformIO, which only needs doing once. The first build also downloads several
   hundred MB of tools.
   ```bash
   python3 -m venv ~/.platformio-venv
   ~/.platformio-venv/bin/pip install platformio
   alias pio=~/.platformio-venv/bin/pio
   ```
   Add that `alias` line to `~/.bashrc` to keep it.
2. Plug in the XIAO, then from the `firmware` folder upload and watch the log:
   ```bash
   cd firmware
   pio run -t upload
   pio device monitor
   ```
3. Check the log shows `boot, wheels: 07:00 off` or `on`, then `wifi: connected`. If it scrolled
   past before the monitor opened, press the board's RESET button.

**If it can't connect to the board:** hold BOOT, tap RESET, release BOOT, then upload again.
Tap RESET once afterwards. **If the board doesn't show up at all**, try another cable first,
because many USB cables only carry power. If you get a permission error, add yourself to the
serial group: `dialout` on Ubuntu and Debian, `uucp` on Arch.

### 6. Test on the bench

With the log still open, and everything still loose on the bench:

1. **Roll each wheel away from you.** The time should go up by one hour or five minutes per
   click. If a wheel runs backwards, flip `INVERT_HOURS` or `INVERT_MINUTES` in
   `firmware/src/config.h` and upload again.
2. **Flip the switch.** If on and off are swapped, flip `SWITCH_ON_WHEN_LOW` in the same file.
3. **Leave it alone for 3 seconds.** The log should print `bridge:` and the time, and the Hue
   app should show the same time.
4. **Check the LEDs** light when you roll a wheel. Try one inside the printed shell before
   gluing it in, because only the lower part of each window gets direct light.

### 7. Assemble

1. Drop the XIAO into the four corner seats with the USB port facing the rear, and hold it with
   a dab of hot glue. Keep glue off the USB port. Stick the antenna inside the rear wall, away
   from the wires.
2. Hot-glue the slide switch into the side slot.
3. Hold the shell upside down. Each LED goes into a slot inside the front slope: lower it
   through the open bottom, dome first, set it into the slot between the two walls, and slide
   it towards the window until its rim stops at the step where the slot narrows. Fix it with a
   dab of hot glue and bend the leads back towards the rear.
   [Picture of the path](docs/renders/led_insert.png).
4. Press each wheel onto its encoder shaft, flat first: hours on the left, minutes on the right.
   It should take a firm push. To take it apart, pull the wheel straight off.
5. Lower each wheel and encoder into the cradles. The bushing goes in the outer U-slot, the stub
   boss in the centre one, and the encoder body in its socket.
6. Slide an M3 nut into the slot in each corner block from the inside, with the flats against
   the slot walls. Add a small dab of hot glue at the slot mouth so it can't fall out, keeping
   glue out of the screw hole.
7. Fit the shell. The lip on the plate holds it in place. Its internal walls come down onto the cradles, so the wheels and encoders
   can't lift out. Before lowering it, lay the encoder and switch wires on the plate behind the
   encoders and run them to the board towards the back, so they pass through the low doorway in
   each rear wall. Run each LED's wires straight back to the board on its own side
   of the centre wall.
8. Fasten from below with the four M3 x 8 screws, then add four dots of hot glue as feet.

If it slides when you roll a wheel, glue some washers or coins inside the front of the base.

### 8. Teach it where the wheels are

The encoders only report movement, not position, so the device has to be told what the windows
show. **Do this once after assembly**, and again whenever the windows and the bridge disagree:

1. Flip the alarm switch three times within 4 seconds. The window LEDs start flashing.
2. Roll the wheels until the windows read **07:00**.
3. Flip the switch once more. The flashing stops.
4. Roll to the time you actually want.

That's four flips, so the switch ends up where it started. If you don't finish within 2
minutes, it cancels and nothing changes. Your alarm is now live, so if you were testing on a
spare automation, go back to step 4 and choose the real one.

## What might need adjusting

These are the known unknowns for a first build:

| What | Why | What to do |
|---|---|---|
| Wheel fit | Dimensions are from the datasheet only | Print one wheel first |
| Faint clicks | The encoder's rated detent force is low at this wheel size | Add a printed spring that rides in the rim ribs |
| Numbers off-centre at a click | The angle between the shaft flat and the detents is unknown | Measure it, set `CLOCK_OFFSET_DEG` in `cad/huewheel.py`, and reprint the wheels |
| Dim windows | Only the lower part of each window gets direct light | Try a lighter filament, though the LEDs may glow through the wall |
| A click counts as nothing or as two | The firmware assumes one full signal cycle per click | Check it in step 6 and fix the decoder if needed |
| Fade timing | It's unknown whether the set time is the start or the end of the fade | Watch a real alarm fire |
| A future bridge update | The automation format isn't publicly documented | If sends start failing, run `plan` with the dry-run tool and check the log |

The firmware doesn't check the bridge's security certificate, because the bridge uses a private
one. Someone on your home network who impersonated the bridge could capture its key.

## For developers

- This repo is public, so turn on the secret checks after cloning. They block commits and pushes
  containing keys, IP addresses or personal details, and the rules are in [`CLAUDE.md`](CLAUDE.md):
  ```bash
  git config core.hooksPath .githooks
  ```
- [`firmware/README.md`](firmware/README.md) has the firmware reference and how to run its
  tests. Tuning values such as timings and LED brightness are in
  [`firmware/src/config.h`](firmware/src/config.h).
- Size is 84 x 84 x 52.6 mm, with 44 mm wheels. All key dimensions are at the top of
  [`cad/huewheel.py`](cad/huewheel.py).

To rebuild the CAD, everything runs in one conda environment (base here) with build123d,
pyvista, trimesh, shapely and rtree installed:

```bash
conda activate base
python cad/huewheel.py      # parts: cad/stl (print-ready), cad/step (untracked)
python cad/assemble.py      # interference check, cad/build meshes, cad/step/assembly.step
python cad/printcheck.py    # supportless-print check
python cad/test/rib_test.py # crush-rib test piece: cad/test/rib_test.stl
python cad/printcheck.py cad/test/rib_test.stl
python cad/test/nut_test.py   # nut slot test: cad/test/nut_test.stl
python cad/test/clamp_test.py # encoder clamp test: cad/test/clamp_test.stl
xvfb-run -a python cad/render.py   # docs/renders
python cad/view.py          # interactive 3D viewer of the assembly
```

Anaconda's VTK bundles its own Mesa without GPU drivers, so on Linux its windows can fail with
"Could not find a decent config". Point it at the system Mesa, and load the system's newer
`libstdc++` and `libdrm`, then reactivate the environment:

```bash
conda env config vars set -n base __GLX_VENDOR_LIBRARY_NAME=mesa \
  LD_PRELOAD="/usr/lib/libstdc++.so.6 /usr/lib/libdrm_amdgpu.so.1 /usr/lib/libdrm.so.2"
```

The `libdrm` entries are for AMD GPUs. If it still fails, run with `LD_DEBUG=libs` to find
the conda library that's older than the system driver needs.
