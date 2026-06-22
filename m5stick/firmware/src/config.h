#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>
#include <driver/i2s.h>

// ===== 蓝牙配置 =====
#define BT_DEVICE_NAME "M5Stick-Claude"
#define BT_SERIAL_BAUD 115200

// ===== 引脚定义 (M5StickC Plus IoT) =====
// PDM 麦克风
#define I2S_PDM_CLK     GPIO_NUM_0
#define I2S_PDM_DATA    GPIO_NUM_34
#define I2S_PDM_WS      GPIO_NUM_26

// 按键 (M5StickC Plus)
#define BUTTON_A_PIN    37  // 正面右键 (确认)
#define BUTTON_B_PIN    39  // 正面左键 / 电源键 (录音/取消)

// RGB LED
#define RGB_LED_PIN     10  // 红色 LED (部分型号可用 SK6812)

// ===== 音频配置 =====
#define AUDIO_SAMPLE_RATE   16000   // 16kHz
#define AUDIO_BITS          16      // 16-bit
#define AUDIO_CHANNELS      1       // 单声道
#define AUDIO_DMA_BUF_CNT   8       // DMA 缓冲区数量
#define AUDIO_DMA_BUF_LEN   256     // 每个 DMA 缓冲区长度 (样本数)
#define AUDIO_CHUNK_SIZE    512     // 每次发送的音频块大小 (字节)
#define AUDIO_MAX_DURATION  10      // 最大录音时长 (秒)
#define AUDIO_LONG_PRESS_MS 1000    // 长按判定时间 (ms)

// ===== 协议帧 Magic =====
#define FRAME_MAGIC     0xCC55

// ===== 帧类型 (Bridge -> M5) =====
#define MSG_DISPLAY_TEXT    0x01
#define MSG_DISPLAY_CONFIRM 0x02
#define MSG_SET_MODE        0x03
#define MSG_START_RECORDING 0x04
#define MSG_STOP_RECORDING  0x05
#define MSG_SHOW_STATUS     0x06

// ===== 帧类型 (M5 -> Bridge) =====
#define MSG_BUTTON_PRESS    0x10
#define MSG_AUDIO_DATA      0x11
#define MSG_RECORDING_DONE  0x12

// ===== 帧类型 (双向) =====
#define MSG_PING            0x20
#define MSG_PONG            0x21

// ===== 设备模式 =====
enum DeviceMode {
    MODE_IDLE = 0,
    MODE_CONFIRM_PENDING = 1,
    MODE_RECORDING = 2,
    MODE_PROCESSING = 3,
};

// ===== 按键 ID =====
#define BTN_A   0x00  // 确认
#define BTN_B   0x01  // 拒绝/停止录音

// ===== 通信模式 =====
// 注释掉以下定义以使用蓝牙模式 (BluetoothSerial)
#define USB_MODE  // 启用 USB 串口通信模式 (通过 USB-C 线缆与 bridge 通信)

// ===== 调试输出 =====
// USB 模式下 Serial 用于二进制帧通信, 不能混入文本调试
#ifdef USB_MODE
  #define DBG_PRINTF(...) ((void)0)
#else
  #define DBG_PRINTF(...) Serial.printf(__VA_ARGS__)
#endif

// ===== 显示参数 =====
#define DISPLAY_WIDTH  135
#define DISPLAY_HEIGHT 240
#define STATUS_BAR_H   16
#define MAX_CMD_LINES  6
#define CMD_CHAR_PER_LINE 22

#endif // CONFIG_H
