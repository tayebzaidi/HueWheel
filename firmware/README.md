# HueWheel firmware

For the Seeed XIAO ESP32C3, built with PlatformIO.

**Status:** first draft. It compiles and the wheel logic passes its PC tests, but it has
not run on a real board or encoder yet.

## Wiring

| Signal | XIAO pin | GPIO | Connect to |
|---|---|---|---|
| Hours encoder A | D1 | 3 | Left encoder, outer pin A |
| Hours encoder B | D2 | 4 | Left encoder, outer pin B |
| Minutes encoder A | D3 | 5 | Right encoder, outer pin A |
| Minutes encoder B | D4 | 6 | Right encoder, outer pin B |
| Alarm switch | D5 | 7 | Slide switch centre lug |
| LEDs | D10 | 10 | Each LED's long leg through its own 220-470 ohm resistor |
| Ground | GND | | Both encoder centre pins (C), one outer switch lug, both LED short legs |

The encoders need no resistors: the firmware turns on the ESP32's internal pull-ups. Leave
the third switch lug unconnected. Leave D0, D8 and D9 free, because they control how the
board boots.

Connect the antenna before using Wi-Fi.

## 1. Install PlatformIO

```bash
python3 -m venv ~/.platformio-venv
~/.platformio-venv/bin/pip install platformio
alias pio=~/.platformio-venv/bin/pio    # add this to ~/.bashrc to keep it
```

The first build downloads the ESP32 toolchain, several hundred MB.

Your account must be able to open the serial port. On Arch that means the `uucp` group,
which you already have. On Debian or Ubuntu the group is `dialout`.

## 2. Add your settings

The Hue values come from the dry run, which also creates `firmware/include/secrets.h`:

```bash
python3 tools/hue_dryrun.py discover
python3 tools/hue_dryrun.py pair      # press the bridge button first
python3 tools/hue_dryrun.py list
python3 tools/hue_dryrun.py use <id>
```

Then type `WIFI_SSID` and `WIFI_PASSWORD` into `secrets.h`. The network must be 2.4 GHz.
That file is ignored by git, but its contents are built into the firmware, so don't share
a compiled `firmware.bin`.

Give the bridge a DHCP reservation in your router. The firmware connects to a fixed IP.

## 3. Build and upload

Connect the XIAO with a USB cable that carries data, then from `firmware/`:

```bash
pio run                  # compile only
pio run -t upload        # compile and flash
pio device monitor       # watch the log; Ctrl-C to quit
```

The board appears as `/dev/ttyACM0`. If you have other serial devices, add
`--upload-port /dev/ttyACM0` to the upload command.

**If the upload can't connect,** force the bootloader: hold BOOT, tap RESET, release BOOT,
then upload again. Tap RESET once afterwards to start the new firmware.

**If the board isn't listed at all,** try another cable first. Charge-only cables are the
usual cause.

## 4. Check it on the bench

A bare board is safe to flash and shows `boot, wheels: 07:00 off` and then `wifi: connected`
with nothing wired up. Then, before gluing anything in:

1. **Wheels:** roll each one away from you and watch the log. The time should go up by 1
   hour or 5 minutes per click. If a wheel runs backwards, flip `INVERT_HOURS` or
   `INVERT_MINUTES` in `src/config.h`. If each click counts as nothing or as two, stop and
   report it: the decoder assumes one full quadrature cycle per detent.
2. **Switch:** flip it and check `on` and `off` match the side you want. If they're swapped,
   flip `SWITCH_ON_WHEN_LOW`.
3. **Bridge:** stop moving things. After 2.5 seconds the log prints `bridge: HH:MM on`, and
   the Hue app shows the new time.

The logic tests need no board. From `firmware/`:

```bash
g++ -std=c++17 -Wall -Wextra -Isrc test/test_logic.cpp -o /tmp/test_logic && /tmp/test_logic
```

## Using it

- Wheels and switch send to the bridge 2.5 seconds after the last change.
- A 100 ms blink every 5 seconds means the bridge doesn't have the latest time yet. It keeps
  retrying, up to once a minute. **Don't trust the alarm while it's blinking.**
- A power cut changes nothing on the bridge. Anything that changed since the last successful
  send goes out after it reconnects.

### Re-sync the wheels

Do this on first use and any time the numbers and the device disagree, for example if a
wheel was turned while unplugged.

1. Flip the alarm switch three times within 4 seconds. The window LEDs start flashing.
2. Roll the wheels until the windows read **07:00**.
3. Flip the switch once more. The LEDs stop flashing and the device now knows the position.
4. Roll to the time you want.

That is four flips, so the switch ends where it started. After 2 minutes without step 3,
re-sync cancels and the position stays as it was.
