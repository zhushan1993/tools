#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <Arduino.h>
#include "config.h"

// ===== 二进制帧结构 =====
// [Magic 2B][Length 2B LE][Type 1B][Payload Length B]
// Magic: 0xCC55

struct FrameHeader {
    uint16_t magic;
    uint16_t length;
    uint8_t  type;
} __attribute__((packed));

// 通信流指针 — 指向 Serial (USB) 或 SerialBT (蓝牙)
extern Stream* comm_stream;

// 设置通信端口
void set_comm_stream(Stream* stream);

// 发送帧
bool send_frame(uint8_t type, const uint8_t* payload, uint16_t length);
bool send_frame(uint8_t type);  // 无 payload

// 尝试读取一帧, 返回 true 如果成功读到完整帧
// 注意: 此函数不会阻塞, 数据不完整时返回 false
bool read_frame(uint8_t* out_type, uint8_t* out_payload, uint16_t* out_length, uint16_t max_len);

// 音频数据缓冲 (PSRAM 分配)
#define AUDIO_BUFFER_SIZE  (AUDIO_MAX_DURATION * AUDIO_SAMPLE_RATE * 2)
extern uint8_t* audio_buffer;
extern const uint32_t audio_buffer_size;
extern volatile uint32_t audio_buffer_pos;

// 重置音频缓冲区
void reset_audio_buffer();

#endif // PROTOCOL_H
