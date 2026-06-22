#include "led.h"

static bool g_blink_enabled = false;
static bool g_led_state = false;
static unsigned long g_blink_interval = 500;
static unsigned long g_last_toggle = 0;

void led_init() {
    pinMode(RGB_LED_PIN, OUTPUT);
    digitalWrite(RGB_LED_PIN, LOW);
}

void led_set(bool on) {
    g_blink_enabled = false;
    g_led_state = on;
    digitalWrite(RGB_LED_PIN, on ? HIGH : LOW);
}

void led_blink(unsigned long interval_ms) {
    g_blink_enabled = true;
    g_blink_interval = interval_ms;
    g_last_toggle = millis();
    g_led_state = true;
    digitalWrite(RGB_LED_PIN, HIGH);
}

void led_update() {
    if (!g_blink_enabled) return;
    unsigned long now = millis();
    if (now - g_last_toggle >= g_blink_interval) {
        g_led_state = !g_led_state;
        digitalWrite(RGB_LED_PIN, g_led_state ? HIGH : LOW);
        g_last_toggle = now;
    }
}
