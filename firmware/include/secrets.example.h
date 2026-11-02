// Copy to secrets.h (git-ignored) and fill in. tools/hue_dryrun.py fills in the
// three HUE_ values for you; only the Wi-Fi lines are typed by hand.
#pragma once

#define WIFI_SSID "your-2.4GHz-network"  // the ESP32-C3 has no 5 GHz radio
#define WIFI_PASSWORD "your-password"

#define HUE_BRIDGE_IP ""  // give the bridge a DHCP reservation so this stays valid
#define HUE_APP_KEY ""
#define HUE_WAKEUP_ID ""  // behavior_instance id of the Wake Up automation to edit
