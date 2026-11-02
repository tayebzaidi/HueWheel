// Host test for src/logic.h; needs no ESP32. From firmware/:
//   g++ -std=c++17 -Wall -Wextra -Isrc test/test_logic.cpp -o /tmp/test_logic && /tmp/test_logic
#include <cassert>
#include <cstdio>
#include <vector>

#include "logic.h"

// One detent's worth of edges with A leading B, starting from pins 00 or 11.
static const std::vector<uint8_t> FORWARD_FROM_00 = {0b10, 0b11, 0b01, 0b00};
static const std::vector<uint8_t> FORWARD_FROM_11 = {0b01, 0b00, 0b10, 0b11};

static int feed(Quadrature& q, const std::vector<uint8_t>& samples) {
  int total = 0;
  for (uint8_t s : samples) total += q.update(s);
  return total;
}

static std::vector<uint8_t> reversed(const std::vector<uint8_t>& cycle, uint8_t rest) {
  std::vector<uint8_t> r(cycle.rbegin() + 1, cycle.rend());
  r.push_back(rest);
  return r;
}

static void test_clicks_either_rest_state() {
  Quadrature a, b;
  a.begin(0b00);
  b.begin(0b11);
  assert(feed(a, FORWARD_FROM_00) == 1);
  assert(feed(b, FORWARD_FROM_11) == 1);
  assert(feed(a, reversed(FORWARD_FROM_00, 0b00)) == -1);
  assert(feed(b, reversed(FORWARD_FROM_11, 0b11)) == -1);
}

static void test_bounce_is_one_click() {
  Quadrature q;
  q.begin(0b00);
  assert(feed(q, {0b10, 0b00, 0b10, 0b11, 0b10, 0b11, 0b01, 0b11, 0b01, 0b00, 0b01, 0b00}) == 1);
}

static void test_rest_chatter_is_no_click() {
  Quadrature q;
  q.begin(0b00);
  assert(feed(q, {0b10, 0b00, 0b01, 0b00, 0b10, 0b00}) == 0);
}

static void test_half_roll_and_back_is_no_click() {
  Quadrature q;
  q.begin(0b00);
  assert(feed(q, {0b10, 0b11, 0b10, 0b00}) == 0);
}

static void test_slow_samples_repeat_harmlessly() {
  Quadrature q;
  q.begin(0b00);
  assert(feed(q, {0b00, 0b10, 0b10, 0b11, 0b11, 0b11, 0b01, 0b00, 0b00}) == 1);
}

static void test_recovers_after_impossible_jump() {
  Quadrature q;
  q.begin(0b00);
  assert(feed(q, {0b11, 0b00}) == 0);
  assert(feed(q, FORWARD_FROM_00) == 1);
}

static void test_alarm_time_wraps() {
  AlarmTime t;
  t.set(23, 55);
  t.rollHours(1);
  t.rollMinutes(1);
  assert(t.hour == 0 && t.minute() == 0);
  t.rollHours(-1);
  t.rollMinutes(-1);
  assert(t.hour == 23 && t.minute() == 55);
  t.rollMinutes(24);  // a full turn of the minutes wheel lands on the same number
  assert(t.minute() == 55);
  t.rollHours(-49);
  assert(t.hour == 22);
}

static void test_flips() {
  FlipCounter f(4000);
  assert(!f.flip(1000) && !f.flip(2000) && f.flip(3000));
  assert(!f.flip(10000) && !f.flip(11000));
  assert(!f.flip(20000));  // too late: this starts a new count
  assert(!f.flip(21000) && f.flip(22000));
  uint32_t nearWrap = 0xFFFFF000;
  assert(!f.flip(nearWrap) && !f.flip(nearWrap + 1000) && f.flip(nearWrap + 6000 - 3000));
}

static void test_debounce() {
  Debounced d(false, 30);
  assert(!d.update(true, 100) && !d.update(false, 105) && !d.update(true, 110));
  assert(!d.update(true, 139));
  assert(d.update(true, 140) && d.state());
  assert(!d.update(true, 200));
}

int main() {
  test_clicks_either_rest_state();
  test_bounce_is_one_click();
  test_rest_chatter_is_no_click();
  test_half_roll_and_back_is_no_click();
  test_slow_samples_repeat_harmlessly();
  test_recovers_after_impossible_jump();
  test_alarm_time_wraps();
  test_flips();
  test_debounce();
  puts("all logic tests passed");
}
