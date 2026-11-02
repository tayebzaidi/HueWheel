#include "hue.h"

#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

#include "secrets.h"

// The bridge's certificate is signed by Signify's private CA, not a public one,
// so this first draft does not verify it. Anyone able to impersonate the bridge
// on your LAN could capture the application key.
//
// The whole configuration is read and written back because it also holds the
// rooms, fade and style set in the Hue app. Only the time is changed. If the
// expected fields are missing nothing is written.

static bool open(HTTPClient& http, WiFiClientSecure& tls) {
  String url = String("https://") + HUE_BRIDGE_IP + "/clip/v2/resource/behavior_instance/" + HUE_WAKEUP_ID;
  if (!http.begin(tls, url)) return false;
  http.addHeader("hue-application-key", HUE_APP_KEY);
  return true;
}

bool hueSetAlarm(const AlarmTime& t, bool enabled) {
  WiFiClientSecure tls;
  tls.setInsecure();
  HTTPClient http;
  http.setTimeout(8000);

  if (!open(http, tls)) return false;
  int code = http.GET();
  if (code != 200) {
    Serial.printf("hue: GET failed: %d\n", code);
    http.end();
    return false;
  }
  String body = http.getString();
  http.end();

  JsonDocument filter;
  filter["data"][0]["configuration"] = true;
  JsonDocument got;
  DeserializationError err = deserializeJson(got, body, DeserializationOption::Filter(filter));
  if (err) {
    Serial.printf("hue: bad JSON: %s\n", err.c_str());
    return false;
  }
  JsonObject time = got["data"][0]["configuration"]["when"]["time_point"]["time"];
  if (time.isNull()) {
    Serial.println("hue: no when.time_point.time in this automation, not writing");
    return false;
  }
  time["hour"] = t.hour;
  time["minute"] = t.minute();

  JsonDocument put;
  put["enabled"] = enabled;
  put["configuration"] = got["data"][0]["configuration"];
  String out;
  serializeJson(put, out);

  if (!open(http, tls)) return false;
  http.addHeader("Content-Type", "application/json");
  code = http.PUT(out);
  String reply = http.getString();
  http.end();
  if (code != 200) {
    Serial.printf("hue: PUT failed: %d %s\n", code, reply.c_str());
    return false;
  }
  return true;
}
