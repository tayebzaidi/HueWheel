// Wiring and tuning. The pin map is also in firmware/README.md.
#pragma once

#include <stdint.h>

// XIAO ESP32C3 labels in the comments. These avoid the strapping pins
// D0 (GPIO2), D8 (GPIO8) and D9 (GPIO9), which can stop the board booting.
constexpr int PIN_HOURS_A = 3;    // D1
constexpr int PIN_HOURS_B = 4;    // D2
constexpr int PIN_MINUTES_A = 5;  // D3
constexpr int PIN_MINUTES_B = 6;  // D4
constexpr int PIN_SWITCH = 7;     // D5, other side of the switch to GND
constexpr int PIN_LED = 10;       // D10

// The encoders are mirror images in the shell, so the same roll turns them
// opposite ways. These are predicted from the CAD: flip one if that wheel runs
// backwards. There's no need to rewire anything.
constexpr bool INVERT_HOURS = false;
constexpr bool INVERT_MINUTES = true;

// Which lug the switch is wired to decides this. Flip it if on and off are swapped.
constexpr bool SWITCH_ON_WHEN_LOW = true;

constexpr uint32_t SWITCH_DEBOUNCE_MS = 30;
constexpr uint32_t SETTLE_MS = 2500;       // quiet time before sending to the bridge
constexpr uint32_t LED_ON_MS = 5000;       // window light after the last click
constexpr uint8_t LED_BRIGHTNESS = 80;     // 0-255; it sits by a bed
constexpr uint32_t RETRY_MIN_MS = 5000;    // first retry after a failed send
constexpr uint32_t RETRY_MAX_MS = 60000;   // doubles up to this
constexpr uint32_t WARN_PERIOD_MS = 5000;  // short blink while the bridge is out of date

// Three switch flips within SYNC_ARM_MS starts re-sync. See firmware/README.md.
constexpr uint32_t SYNC_ARM_MS = 4000;
constexpr uint32_t SYNC_TIMEOUT_MS = 120000;
constexpr uint8_t SYNC_HOUR = 7;     // what the windows must read when confirming:
constexpr uint8_t SYNC_MINUTE = 0;   // a sane alarm if nothing else gets set afterwards
