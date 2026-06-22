#include "buttons.h"

// 按键消抖和长按检测的私有状态
static bool g_last_a = HIGH;
static bool g_last_b = HIGH;
static unsigned long g_b_press_ms = 0;
static bool g_b_long_reported = false;

void buttons_init() {
    pinMode(BUTTON_A_PIN, INPUT_PULLUP);
    pinMode(BUTTON_B_PIN, INPUT_PULLUP);
    g_last_a = digitalRead(BUTTON_A_PIN);
    g_last_b = digitalRead(BUTTON_B_PIN);
}

ButtonEvent buttons_poll() {
    bool a = digitalRead(BUTTON_A_PIN);
    bool b = digitalRead(BUTTON_B_PIN);

    // ---- A 键: 按下即触发 ----
    if (g_last_a == HIGH && a == LOW) {
        g_last_a = a;
        g_last_b = b;
        return BTN_EVENT_A_PRESS;
    }

    // ---- B 键: 区分短按和长按 ----
    if (g_last_b == HIGH && b == LOW) {
        // 按下 B
        g_b_press_ms = millis();
        g_b_long_reported = false;
    }

    if (g_last_b == LOW && b == LOW) {
        // 持续按住 B — 检查长按
        if (!g_b_long_reported && (millis() - g_b_press_ms > AUDIO_LONG_PRESS_MS)) {
            g_b_long_reported = true;
            g_last_a = a;
            g_last_b = b;
            return BTN_EVENT_B_LONG;
        }
    }

    if (g_last_b == LOW && b == HIGH) {
        // 释放 B
        if (!g_b_long_reported) {
            g_last_a = a;
            g_last_b = b;
            return BTN_EVENT_B_SHORT;
        }
    }

    g_last_a = a;
    g_last_b = b;
    return BTN_EVENT_NONE;
}
