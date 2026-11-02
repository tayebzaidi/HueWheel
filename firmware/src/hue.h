// Edits one Wake Up automation on the Hue Bridge (CLIP v2).
#pragma once

#include <Arduino.h>

#include "logic.h"

// Reads the automation, changes the time and on/off, and writes it back.
// Returns true once the bridge has accepted the change.
bool hueSetAlarm(const AlarmTime& t, bool enabled);
