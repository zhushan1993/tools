#ifndef DISPLAY_H
#define DISPLAY_H

#include <Arduino.h>
#include <M5StickCPlus.h>
#include "config.h"

// 初始化屏幕 (旋转方向、清屏)
void display_init();

// 状态栏 (屏幕顶部色条)
void display_status_bar(const char* text, uint16_t color);

// ===== 各模式界面 =====
// 待机界面
void display_idle(bool bt_connected, const char* device_name);

// 授权确认界面
void display_confirm(const char* tool, const char* cmd);

// 录音界面
void display_recording(unsigned long elapsed, unsigned long max_duration);

// STT 识别中界面
void display_processing();

// 纯文本显示
void display_text(const char* text);

// 全屏单色消息 (用于确认/拒绝/错误等)
void display_message(const char* text, uint16_t bg_color, uint16_t text_color);

#endif // DISPLAY_H
