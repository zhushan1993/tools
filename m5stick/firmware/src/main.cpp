/**
 * M5StickC Plus IoT — Claude Code 便携化终端
 *
 * 通过经典蓝牙 SPP 与电脑上的 Bridge Server 通信，
 * 实现物理按键授权确认和语音输入功能。
 *
 * == 依赖模块 ==
 *   config.h    — 引脚和协议常量
 *   protocol.h  — 蓝牙帧编解码
 *   audio.h     — PDM 麦克风驱动
 *   display.h   — 屏幕界面
 *   buttons.h   — 按键输入
 *   led.h       — LED 指示
 */

#include <M5StickCPlus.h>
#include <BluetoothSerial.h>
#include "config.h"
#include "protocol.h"
#include "audio.h"
#include "display.h"
#include "buttons.h"
#include "led.h"

#ifndef USB_MODE
BluetoothSerial SerialBT;
#endif

// ===== 设备状态 =====
static DeviceMode current_mode = MODE_IDLE;
static bool bt_connected = false;
static unsigned long last_ping_ms = 0;
static unsigned long recording_start_ms = 0;

// 当前确认请求信息
static char current_tool[32] = {0};
static char current_cmd[256] = {0};
static char current_req_id[64] = {0};

// ===== 函数声明 =====
static void handle_serial_commands();
static void handle_event_a_press();
static void handle_event_b_short();
static void handle_event_b_long();
static void enter_idle_mode();
static void enter_confirm_mode();
static void enter_recording_mode();
static void stop_recording();
static void process_audio();

// ===== 按键事件处理 =====

static void handle_event_a_press() {
    if (current_mode == MODE_CONFIRM_PENDING) {
        // 用户确认授权
        uint8_t payload[1] = {BTN_A};
        send_frame(MSG_BUTTON_PRESS, payload, 1);
        display_message("已确认", TFT_GREEN, TFT_WHITE);
        current_mode = MODE_IDLE;
        display_idle(bt_connected, BT_DEVICE_NAME);
    }
}

static void handle_event_b_short() {
    if (current_mode == MODE_CONFIRM_PENDING) {
        // 用户拒绝授权
        uint8_t payload[1] = {BTN_B};
        send_frame(MSG_BUTTON_PRESS, payload, 1);
        display_message("已拒绝", TFT_RED, TFT_WHITE);
        current_mode = MODE_IDLE;
        display_idle(bt_connected, BT_DEVICE_NAME);
    } else if (current_mode == MODE_RECORDING) {
        // 停止录音
        stop_recording();
    } else if (current_mode == MODE_IDLE) {
        // 空闲时短按 B 开始录音
        enter_recording_mode();
    }
}

static void handle_event_b_long() {
    // 长按 B (电源键) 由 AXP192 硬件处理关机 (~2s), 固件不干预
    (void)current_mode;
}

// ===== 模式切换 =====

static void enter_idle_mode() {
    current_mode = MODE_IDLE;
    led_set(false);
    display_idle(bt_connected, BT_DEVICE_NAME);
}

static void enter_confirm_mode() {
    current_mode = MODE_CONFIRM_PENDING;
    led_set(true);  // 常亮提醒用户操作
    display_confirm(current_tool, current_cmd);
}

static void enter_recording_mode() {
    audio_start();
    recording_start_ms = millis();
    current_mode = MODE_RECORDING;
    led_set(true);  // 录音时亮起

    uint8_t duration = AUDIO_MAX_DURATION;
    send_frame(MSG_START_RECORDING, &duration, 1);
    display_recording(0, AUDIO_MAX_DURATION);
}

static void stop_recording() {
    audio_stop();
    send_frame(MSG_RECORDING_DONE, (uint8_t*)&audio_buffer_pos, sizeof(audio_buffer_pos));
    current_mode = MODE_PROCESSING;
    led_blink(200);  // 快速闪烁表示 STT 处理中
    display_processing();
}

// ===== 蓝牙命令处理 =====

static void handle_serial_commands() {
    static uint8_t payload[512];
    uint16_t length = 0;
    uint8_t type;

    while (read_frame(&type, payload, &length, sizeof(payload))) {
        payload[length] = '\0';  // 字符串终止

        switch (type) {
            case MSG_DISPLAY_TEXT:
                display_text((char*)payload);
                break;

            case MSG_DISPLAY_CONFIRM: {
                // 简单 JSON 解析: {"tool":"...","cmd":"...","id":"..."}
                char* p = (char*)payload;
                char* tool_start = strstr(p, "\"tool\":\"");
                char* cmd_start = strstr(p, "\"cmd\":\"");
                char* id_start = strstr(p, "\"id\":\"");
                if (tool_start) {
                    sscanf(tool_start + 8, "%[^\"]", current_tool);
                }
                if (cmd_start) {
                    sscanf(cmd_start + 6, "%[^\"]", current_cmd);
                }
                if (id_start) {
                    sscanf(id_start + 5, "%[^\"]", current_req_id);
                }
                enter_confirm_mode();
                break;
            }

            case MSG_SET_MODE:
                if (length >= 1) {
                    current_mode = (DeviceMode)payload[0];
                    if (current_mode == MODE_IDLE) {
                        led_set(false);
                        display_idle(bt_connected, BT_DEVICE_NAME);
                    }
                }
                break;

            case MSG_SHOW_STATUS:
                display_status_bar((char*)payload, TFT_DARKGREY);
                break;

            case MSG_STOP_RECORDING:
                if (current_mode == MODE_RECORDING) {
                    stop_recording();
                }
                break;

            case MSG_PING:
                send_frame(MSG_PONG, payload, length);
                break;

            default:
                break;
        }
    }
}

// ===== 音频采集处理 =====

static void process_audio() {
    audio_process_tick();  // 从 I2S PDM 麦克风读取数据并发送
}

// ===== 入口 =====

void setup() {
    M5.begin();

    // B 键长按由 AXP192 硬件处理 (约 2 秒后关机), 固件不干预

    display_init();
    buttons_init();
    led_init();

    // LED 启动自检: 新固件闪烁 5 次
    for (int i = 0; i < 5; i++) {
        led_set(true);
        delay(100);
        led_set(false);
        delay(100);
    }

#ifdef USB_MODE
    // ===== USB 串口模式 =====
    Serial.begin(BT_SERIAL_BAUD);
    set_comm_stream(&Serial);
    bt_connected = true;  // USB 始终在线

    // 在 audio_init 之前就显示 idle 界面——即使麦克风初始化失败也不影响屏幕
    display_idle(true, BT_DEVICE_NAME);
#else
    // BT 模式下先显示启动信息, 连接后会自动进入 idle 界面
#endif

    // 初始化 PDM 麦克风
    if (!audio_init()) {
        display_message("麦克风初始化失败", TFT_RED, TFT_WHITE);
        delay(2000);
    }

#ifdef USB_MODE
    // USB 模式下已在上方调用了 display_idle
#else
    // ===== 蓝牙模式 =====
    M5.Lcd.setTextSize(1);
    M5.Lcd.setCursor(5, 80);
    M5.Lcd.println("启动蓝牙...");
    M5.Lcd.setCursor(5, 100);
    M5.Lcd.print("设备名: ");
    M5.Lcd.println(BT_DEVICE_NAME);

    // 启动蓝牙 SPP
    SerialBT.begin(BT_DEVICE_NAME);
    set_comm_stream(&SerialBT);

    M5.Lcd.setCursor(5, 130);
    M5.Lcd.println("请用电脑配对");
    M5.Lcd.setCursor(5, 150);
    M5.Lcd.println("配对后运行 Bridge");
#endif
}

void loop() {
    M5.update();
    led_update();  // 驱动 LED 闪烁

#ifndef USB_MODE
    // ---- 蓝牙连接状态 (仅蓝牙模式) ----
    {
        static unsigned long reconnect_dot_ms = 0;
        static int dot_count = 0;

        bool was_connected = bt_connected;
        bt_connected = SerialBT.hasClient();
        if (bt_connected != was_connected) {
            if (bt_connected) {
                // 恢复连接
                if (current_mode != MODE_IDLE) {
                    // 断开时未完成的操作自动终止
                    if (current_mode == MODE_RECORDING) {
                        audio_stop();
                    }
                    current_mode = MODE_IDLE;
                }
                led_set(false);
                display_status_bar("蓝牙已连接", TFT_GREEN);
                delay(1000);
                display_idle(bt_connected, BT_DEVICE_NAME);
            } else {
                // 失去连接 → 模式复位 + LED 慢闪
                if (current_mode == MODE_RECORDING) {
                    audio_stop();
                }
                current_mode = MODE_IDLE;
                led_blink(500);

                M5.Lcd.fillScreen(TFT_BLACK);
                M5.Lcd.setTextSize(1);
                M5.Lcd.setTextColor(TFT_RED, TFT_BLACK);
                M5.Lcd.setCursor(5, 50);
                M5.Lcd.println("蓝牙已断开");
                M5.Lcd.setTextColor(TFT_DARKGREY, TFT_BLACK);
                M5.Lcd.setCursor(5, 75);
                M5.Lcd.printf("设备: %s", BT_DEVICE_NAME);
                M5.Lcd.setCursor(5, 95);
                M5.Lcd.println("请重新配对或运行 Bridge");
                reconnect_dot_ms = millis();
                dot_count = 0;
            }
        } else if (!bt_connected) {
            // 断开期间 — 动态 "重连中." 指示
            if (millis() - reconnect_dot_ms > 800) {
                dot_count = (dot_count + 1) % 4;
                M5.Lcd.setTextColor(TFT_DARKGREY, TFT_BLACK);
                M5.Lcd.fillRect(5, 115, 120, 12, TFT_BLACK);
                M5.Lcd.setCursor(5, 115);
                M5.Lcd.print("重连中");
                for (int i = 0; i < dot_count; i++) M5.Lcd.print(".");
                reconnect_dot_ms = millis();
            }
        }
    }
#endif

    // ---- 蓝牙命令处理 ----
    if (bt_connected) {
        handle_serial_commands();
    }

    // ---- 按键处理 ----
    ButtonEvent evt = buttons_poll();
    switch (evt) {
        case BTN_EVENT_A_PRESS:
            handle_event_a_press();
            break;
        case BTN_EVENT_B_SHORT:
            handle_event_b_short();
            break;
        case BTN_EVENT_B_LONG:
            handle_event_b_long();
            break;
        default:
            break;
    }

    // ---- 音频处理 ----
    if (current_mode == MODE_RECORDING) {
        process_audio();
        audio_check_health();  // 监控 I2S 状态, 异常时自动恢复
        // 录音超时检查
        if ((millis() - recording_start_ms) > (AUDIO_MAX_DURATION * 1000)) {
            stop_recording();
        }
    }

    // ---- 保持连接 (每 10s 发 ping) ----
    if (bt_connected && (millis() - last_ping_ms > 10000)) {
        uint32_t ts = millis();
        send_frame(MSG_PING, (uint8_t*)&ts, sizeof(ts));
        last_ping_ms = millis();
    }

    delay(20);  // ~50fps 轮询
}
