// HueWheel: two encoder wheels and a switch set a Philips Hue wake-up time.
//
// The wheels are the source of truth. The firmware tracks what they show and
// what the bridge last accepted, and sends whenever the two differ and the
// wheels have gone quiet. Both are saved, so a power cut neither loses the
// position nor overwrites a change made in the Hue app.

#include <Arduino.h>
#include <Preferences.h>
#include <WiFi.h>

#include "config.h"
#include "hue.h"
#include "logic.h"
#include "secrets.h"

struct Alarm {
  AlarmTime time;
  bool enabled = false;
  bool operator==(const Alarm& o) const { return time == o.time && enabled == o.enabled; }
  bool operator!=(const Alarm& o) const { return !(*this == o); }
};

static Preferences prefs;
static Alarm wanted;  // what the wheels and switch show
static Alarm sent;    // what the bridge last accepted
static Alarm saved;   // what is in flash

// Running click totals. Only the encoder task writes these, and a 32-bit store
// is atomic, so loop() can read them without a lock.
static volatile int32_t hourClicks = 0;
static volatile int32_t minuteClicks = 0;
static int32_t hourSeen = 0;
static int32_t minuteSeen = 0;

static uint32_t lastChange = 0;
static uint32_t ledStart = 0;  // starts at 0, so the windows light briefly at power-on
static Debounced alarmSwitch(false, SWITCH_DEBOUNCE_MS);
static uint32_t lastTry = 0;
static uint32_t retryWait = 0;  // 0 means the last send worked, or there hasn't been one
static bool syncing = false;
static uint32_t syncStarted = 0;
static FlipCounter flips(SYNC_ARM_MS);

static uint8_t readPins(int a, int b) {
  return (digitalRead(a) << 1) | digitalRead(b);
}

static void encoderTask(void*) {
  Quadrature hours, minutes;
  hours.begin(readPins(PIN_HOURS_A, PIN_HOURS_B));
  minutes.begin(readPins(PIN_MINUTES_A, PIN_MINUTES_B));
  for (;;) {
    int h = hours.update(readPins(PIN_HOURS_A, PIN_HOURS_B));
    int m = minutes.update(readPins(PIN_MINUTES_A, PIN_MINUTES_B));
    if (h) hourClicks = hourClicks + (INVERT_HOURS ? -h : h);
    if (m) minuteClicks = minuteClicks + (INVERT_MINUTES ? -m : m);
    vTaskDelay(1);  // 1 ms tick; a fast roll is still several ms per edge
  }
}

static bool readSwitch() {
  return (digitalRead(PIN_SWITCH) == LOW) == SWITCH_ON_WHEN_LOW;
}

static void led(uint8_t level) {
  analogWrite(PIN_LED, level);
}

static void saveAlarm(const char* key, const Alarm& a) {
  uint8_t raw[3] = {a.time.hour, a.time.fiveMin, a.enabled};
  prefs.putBytes(key, raw, sizeof raw);
}

static bool loadAlarm(const char* key, Alarm& a) {
  uint8_t raw[3];
  if (prefs.getBytes(key, raw, sizeof raw) != sizeof raw) return false;
  a.time.hour = raw[0] % 24;
  a.time.fiveMin = raw[1] % 12;
  a.enabled = raw[2];
  return true;
}

static void printAlarm(const char* label, const Alarm& a) {
  Serial.printf("%s %02u:%02u %s\n", label, a.time.hour, a.time.minute(), a.enabled ? "on" : "off");
}

static void finishSync(uint32_t now, bool confirmed) {
  syncing = false;
  hourSeen = hourClicks;  // the rolling done during sync doesn't count
  minuteSeen = minuteClicks;
  if (confirmed) {
    wanted.time.set(SYNC_HOUR, SYNC_MINUTE);
    Serial.println("sync: confirmed");
  } else {
    Serial.println("sync: timed out, position unchanged");
  }
  lastChange = now;
  ledStart = now;
}

static void pollInputs(uint32_t now) {
  if (alarmSwitch.update(readSwitch(), now)) {
    wanted.enabled = alarmSwitch.state();
    lastChange = now;
    if (syncing) {
      finishSync(now, true);
    } else if (flips.flip(now)) {
      syncing = true;
      syncStarted = now;
      Serial.printf("sync: roll to %02u:%02u then flip the switch\n", SYNC_HOUR, SYNC_MINUTE);
    }
  }

  int32_t h = hourClicks, m = minuteClicks;
  if (h == hourSeen && m == minuteSeen) return;
  int dh = h - hourSeen, dm = m - minuteSeen;
  hourSeen = h;
  minuteSeen = m;
  ledStart = now;
  if (syncing) return;
  wanted.time.rollHours(dh);
  wanted.time.rollMinutes(dm);
  lastChange = now;
  printAlarm("wheels:", wanted);
}

static void updateLed(uint32_t now) {
  if (syncing) {
    led(now % 800 < 400 ? LED_BRIGHTNESS : 0);
  } else if (now - ledStart < LED_ON_MS) {
    led(LED_BRIGHTNESS);
  } else if (wanted != sent && now - lastChange >= SETTLE_MS) {
    led(now % WARN_PERIOD_MS < 100 ? LED_BRIGHTNESS : 0);  // the alarm on the bridge is stale
  } else {
    led(0);
  }
}

static void pushIfNeeded(uint32_t now) {
  if (syncing || wanted == sent) return;
  if (now - lastChange < SETTLE_MS) return;
  if (wanted != saved) {
    saveAlarm("wanted", wanted);
    saved = wanted;
  }
  if (retryWait && now - lastTry < retryWait) return;

  Alarm attempt = wanted;
  bool connected = WiFi.status() == WL_CONNECTED;
  bool ok = connected && hueSetAlarm(attempt.time, attempt.enabled);
  if (ok) {
    sent = attempt;
    saveAlarm("sent", sent);
    retryWait = 0;
    printAlarm("bridge:", sent);
  } else {
    retryWait = retryWait ? min(retryWait * 2, RETRY_MAX_MS) : RETRY_MIN_MS;
    lastTry = millis();
    Serial.printf("send failed, retrying in %lu ms\n", (unsigned long)retryWait);
    if (!connected) WiFi.reconnect();
  }
}

static void logWifi() {
  static bool was = false;
  bool is = WiFi.status() == WL_CONNECTED;
  if (is == was) return;
  was = is;
  if (is) {
    Serial.printf("wifi: connected as %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("wifi: disconnected");
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(PIN_HOURS_A, INPUT_PULLUP);
  pinMode(PIN_HOURS_B, INPUT_PULLUP);
  pinMode(PIN_MINUTES_A, INPUT_PULLUP);
  pinMode(PIN_MINUTES_B, INPUT_PULLUP);
  pinMode(PIN_SWITCH, INPUT_PULLUP);
  pinMode(PIN_LED, OUTPUT);
  led(0);

  prefs.begin("huewheel");
  wanted.time.set(SYNC_HOUR, SYNC_MINUTE);
  loadAlarm("wanted", wanted);
  saved = wanted;
  alarmSwitch = Debounced(readSwitch(), SWITCH_DEBOUNCE_MS);
  wanted.enabled = alarmSwitch.state();
  if (!loadAlarm("sent", sent)) sent = wanted;  // first boot: nothing to send until something moves
  printAlarm("boot, wheels:", wanted);

  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  xTaskCreate(encoderTask, "encoders", 2048, nullptr, 5, nullptr);
}

void loop() {
  uint32_t now = millis();
  logWifi();
  pollInputs(now);
  if (syncing && now - syncStarted > SYNC_TIMEOUT_MS) finishSync(now, false);
  pushIfNeeded(now);
  updateLed(now);
  delay(5);
}
