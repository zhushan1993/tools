#ifndef BUTTONS_H
#define BUTTONS_H

#include <Arduino.h>
#include "config.h"

// ===== 按键事件 =====
typedef enum {
    BTN_EVENT_NONE = 0,
    BTN_EVENT_A_PRESS,     // A 键按下
    BTN_EVENT_B_SHORT,     // B 键短按（从按下到释放 < 1s）
    BTN_EVENT_B_LONG,      // B 键长按（>= 1s）
} ButtonEvent;

// 初始化按键引脚
void buttons_init();

// 轮询按键状态，返回当前 tick 的事件
// 应每 ~20ms 调用一次
ButtonEvent buttons_poll();

#endif // BUTTONS_H
