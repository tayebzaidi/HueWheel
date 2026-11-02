// Hardware-free logic, so it can be tested on a PC (test/test_logic.cpp).
#pragma once

#include <stdint.h>

// Decodes one encoder sampled at about 1 kHz. Each detent of the PEC11R-xx0024
// is a full quadrature cycle, four edges long, and it rests in the same pin
// state at every detent.
//
// Contact bounce walks back and forth along the cycle and cancels out, and an
// impossible jump (both pins changing between samples) is ignored. A click only
// counts on returning to the rest state, which also clears any miscounted edges.
class Quadrature {
 public:
  void begin(uint8_t pins) {  // pins = (A << 1) | B, sampled while at a detent
    last_ = rest_ = pins;
    travel_ = 0;
  }

  // Returns +1 or -1 on a completed click, otherwise 0. +1 means A led B.
  int8_t update(uint8_t pins) {
    static const int8_t STEP[16] = {0,  -1, 1, 0,  //
                                    1,  0,  0, -1,  //
                                    -1, 0,  0, 1,  //
                                    0,  1,  -1, 0};
    travel_ += STEP[(last_ << 2) | pins];
    last_ = pins;
    if (pins != rest_) return 0;
    int8_t click = travel_ >= 3 ? 1 : travel_ <= -3 ? -1 : 0;
    travel_ = 0;
    return click;
  }

 private:
  uint8_t last_ = 0;
  uint8_t rest_ = 0;
  int8_t travel_ = 0;
};

// Wheel position in clicks. Hours wrap at 24; the minutes wheel prints 00-55
// twice around its 24 positions, so it wraps at 12 clicks of 5 minutes.
struct AlarmTime {
  uint8_t hour = 0;
  uint8_t fiveMin = 0;  // 0-11

  void set(uint8_t h, uint8_t minute) {
    hour = wrap(h, 24);
    fiveMin = wrap(minute / 5, 12);
  }
  void rollHours(int clicks) { hour = wrap(hour + clicks, 24); }
  void rollMinutes(int clicks) { fiveMin = wrap(fiveMin + clicks, 12); }
  uint8_t minute() const { return fiveMin * 5; }

  bool operator==(const AlarmTime& o) const { return hour == o.hour && fiveMin == o.fiveMin; }

 private:
  static uint8_t wrap(int v, int n) { return ((v % n) + n) % n; }
};

// Debounces the slide switch. update() returns true when the settled state changes.
class Debounced {
 public:
  Debounced(bool state, uint32_t holdMs) : state_(state), raw_(state), hold_(holdMs) {}

  bool update(bool raw, uint32_t now) {
    if (raw != raw_) {
      raw_ = raw;
      since_ = now;
    }
    if (raw_ == state_ || now - since_ < hold_) return false;
    state_ = raw_;
    return true;
  }
  bool state() const { return state_; }

 private:
  bool state_;
  bool raw_;
  uint32_t hold_;
  uint32_t since_ = 0;
};

// Spots three flips of the alarm switch inside a time window.
class FlipCounter {
 public:
  explicit FlipCounter(uint32_t windowMs) : window_(windowMs) {}

  // Call on each flip. True on the third flip within the window.
  bool flip(uint32_t now) {
    if (count_ == 0 || now - first_ > window_) {
      first_ = now;
      count_ = 0;
    }
    if (++count_ < 3) return false;
    count_ = 0;
    return true;
  }

 private:
  uint32_t window_;
  uint32_t first_ = 0;
  uint8_t count_ = 0;
};
