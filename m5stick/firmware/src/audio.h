#ifndef AUDIO_H
#define AUDIO_H

#include <Arduino.h>
#include "config.h"

/**
 * M5StickC Plus IoT PDM 麦克风驱动
 *
 * 使用 ESP32 I2S 外设在 PDM RX 模式下采集板载 PDM 麦克风，
 * 输出 16-bit 16kHz 单声道 PCM 数据。
 *
 * 引脚映射 (定义于 config.h):
 *   I2S_PDM_CLK  = GPIO0   — PDM 时钟 (由 ESP32 输出)
 *   I2S_PDM_DATA = GPIO34  — PDM 数据流 (来自麦克风)
 *
 * PDM → PCM 转换由 ESP32 I2S 硬件的抽取滤波器(decimation filter)自动完成。
 */

// ===== 初始化 =====

// 初始化 I2S 驱动并配置 PDM RX 模式
// 返回 true 表示成功
bool audio_init();

// ===== 录音会话 =====

// 开始录音: 清空 DMA 缓冲并重置音频缓冲区
void audio_start();

// 停止录音: 清空 DMA 缓冲
void audio_stop();

// ===== 数据采集 =====

// 从 I2S 读取最多 max_size 字节的 PCM 数据
// 超时 10ms 以避免阻塞主循环
// 返回实际读取的字节数
uint32_t audio_read(uint8_t* buffer, uint32_t max_size);

// 主循环 tick: 从 I2S 读取 PCM 数据,
// 存入全局 audio_buffer 并通过蓝牙发送 MSG_AUDIO_DATA 帧
void audio_process_tick();

// I2S 健康检查: 如果连续失败超过阈值则自动复位驱动
void audio_check_health();

#endif // AUDIO_H
