#ifndef LED_H
#define LED_H

#include <Arduino.h>
#include "config.h"

// 初始化 RGB LED 引脚
void led_init();

// 设置 LED 常亮/常灭
void led_set(bool on);

// 设置 LED 闪烁 (interval_ms: 闪烁间隔毫秒)
void led_blink(unsigned long interval_ms);

// 周期性调用以驱动闪烁, 应每 ~20ms 调用一次
void led_update();

#endif // LED_H
