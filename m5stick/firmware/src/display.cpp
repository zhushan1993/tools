/**
 * 屏幕界面模块 (M5StickC Plus ST7789v2 135×240 TFT)
 *
 * 负责所有屏幕渲染逻辑, 与主状态机解耦。
 * 每个界面函数仅负责绘制, 不修改状态机变量。
 */

#include "display.h"

void display_init() {
    M5.Lcd.setRotation(1);  // USB 口朝上
    M5.Lcd.fillScreen(TFT_BLACK);
    M5.Lcd.setTextSize(1);
    M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
}

void display_status_bar(const char* text, uint16_t color) {
    M5.Lcd.fillRect(0, 0, DISPLAY_WIDTH, STATUS_BAR_H, color);
    M5.Lcd.setTextColor(TFT_WHITE, color);
    M5.Lcd.setCursor(2, 2);
    M5.Lcd.printf("%s", text);
}

void display_idle(bool bt_connected, const char* device_name) {
    (void)device_name;
    M5.Lcd.fillScreen(TFT_BLACK);
    M5.Lcd.setTextSize(3);
    M5.Lcd.setTextColor(TFT_YELLOW, TFT_BLACK);
    M5.Lcd.setCursor(5, 20);
    M5.Lcd.println("Claude");
    M5.Lcd.setCursor(5, 50);
    M5.Lcd.println("Code");

    M5.Lcd.drawFastHLine(5, 80, M5.Lcd.width() - 10, TFT_DARKGREY);

    M5.Lcd.setTextSize(2);
    M5.Lcd.setTextColor(TFT_CYAN, TFT_BLACK);
    M5.Lcd.setCursor(5, 95);
#ifdef USB_MODE
    (void)bt_connected;
    M5.Lcd.print("USB: OK");
#else
    M5.Lcd.printf("BT: %s", bt_connected ? "OK" : "NO");
#endif

    M5.Lcd.setTextSize(2);
    M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
    M5.Lcd.setCursor(5, 116);
    M5.Lcd.print("B=录音");
}

void display_confirm(const char* tool, const char* cmd) {
    M5.Lcd.fillScreen(TFT_BLACK);
    display_status_bar("需要授权", TFT_ORANGE);

    M5.Lcd.setTextSize(1);
    M5.Lcd.setTextColor(TFT_YELLOW, TFT_BLACK);
    M5.Lcd.setCursor(5, STATUS_BAR_H + 4);
    M5.Lcd.printf("%s", tool);

    M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
    M5.Lcd.setCursor(5, STATUS_BAR_H + 20);

    // 命令文本自动换行
    int line = 0;
    const char* p = cmd;
    const char* line_start = cmd;
    while (*p && line < MAX_CMD_LINES) {
        if (*p == '\n' || (p - line_start) >= CMD_CHAR_PER_LINE) {
            int len = (int)(p - line_start);
            // 不能直接修改 const char*, 改用临时打印
            // use Print class write since TFT_eSPI hides it
            ((Print&)M5.Lcd).write((const uint8_t*)line_start, len);
            M5.Lcd.println();
            line_start = (*p == '\n') ? (p + 1) : p;
            p = line_start;
            line++;
        } else {
            p++;
        }
    }
    if (*line_start && line < MAX_CMD_LINES) {
        M5.Lcd.println(line_start);
    }

    // 按钮提示
    M5.Lcd.fillRoundRect(10, DISPLAY_HEIGHT - 40, 50, 30, 4, TFT_GREEN);
    M5.Lcd.setTextColor(TFT_WHITE, TFT_GREEN);
    M5.Lcd.setCursor(18, DISPLAY_HEIGHT - 34);
    M5.Lcd.print("A 确认");

    M5.Lcd.fillRoundRect(75, DISPLAY_HEIGHT - 40, 50, 30, 4, TFT_RED);
    M5.Lcd.setTextColor(TFT_WHITE, TFT_RED);
    M5.Lcd.setCursor(83, DISPLAY_HEIGHT - 34);
    M5.Lcd.print("B 拒绝");
}

void display_recording(unsigned long elapsed, unsigned long max_duration) {
    M5.Lcd.fillScreen(TFT_BLACK);
    display_status_bar("录音中...", TFT_BLUE);

    M5.Lcd.setTextSize(2);
    M5.Lcd.setTextColor(TFT_CYAN, TFT_BLACK);
    M5.Lcd.setCursor(20, 60);
    M5.Lcd.println("REC");

    // 进度条
    uint16_t bar_width = DISPLAY_WIDTH - 20;
    uint16_t fill = (elapsed * bar_width) / max_duration;
    if (fill > bar_width) fill = bar_width;

    M5.Lcd.drawRect(10, 100, bar_width, 12, TFT_WHITE);
    M5.Lcd.fillRect(10, 100, fill, 12, TFT_BLUE);

    M5.Lcd.setTextSize(1);
    M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
    M5.Lcd.setCursor(10, 130);
    M5.Lcd.printf("%ds / %ds", (int)elapsed, (int)max_duration);
    M5.Lcd.setCursor(10, 160);
    M5.Lcd.println("按 B 停止");
}

void display_processing() {
    M5.Lcd.fillScreen(TFT_BLACK);
    display_status_bar("识别中...", TFT_PURPLE);

    M5.Lcd.setTextSize(2);
    M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
    M5.Lcd.setCursor(15, 90);
    M5.Lcd.println("请稍候");
}

void display_text(const char* text) {
    M5.Lcd.fillScreen(TFT_BLACK);
    M5.Lcd.setCursor(5, 5);
    M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
    M5.Lcd.println(text);
}

void display_message(const char* text, uint16_t bg_color, uint16_t text_color) {
    M5.Lcd.fillScreen(bg_color);
    M5.Lcd.setTextSize(2);
    M5.Lcd.setTextColor(text_color, bg_color);
    M5.Lcd.setCursor(20, 100);
    M5.Lcd.println(text);
    delay(500);
}
