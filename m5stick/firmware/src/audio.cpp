/**
 * M5StickC Plus IoT — PDM 麦克风驱动 (I2S)
 *
 * 使用 ESP32 I2S 外设的 PDM RX 模式采集板载 PDM 麦克风。
 *
 * ## PDM 原理
 *   PDM (Pulse Density Modulation) 麦克风输出 1-bit 位流，
 *   ESP32 的 I2S 硬件通过抽取滤波器(decimation filter)将其转换为
 *   16-bit PCM 数据，无需软件干预。
 *
 * ## 硬件连接 (M5StickC Plus IoT)
 *   GPIO0  — I2S_WS / PDM 时钟输出 (1.024 MHz @ 16kHz × 64)
 *   GPIO34 — PDM 数据输入
 *
 * ## 输出格式
 *   16-bit, 16kHz, 单声道, 小端 PCM
 */

#include "audio.h"
#include "protocol.h"
#include <driver/i2s.h>

static const i2s_port_t I2S_PORT = I2S_NUM_0;
static bool g_initialized = false;

// 错误监控
static int g_i2s_err_count = 0;
static const int I2S_ERR_THRESHOLD = 50;  // 连续 50 次失败后尝试复位
static unsigned long g_last_read_ok_ms = 0;

// ===== 初始化 =====

bool audio_init() {
    if (g_initialized) return true;

    // ---- I2S 驱动配置 ----
    // PDM RX 模式下:
    //   - I2S_MODE_PDM 启用 PDM 模式
    //   - I2S_MODE_RX  接收方向
    //   - I2S_MODE_MASTER ESP32 提供时钟
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX | I2S_MODE_PDM),
        .sample_rate = AUDIO_SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = AUDIO_DMA_BUF_CNT,
        .dma_buf_len = AUDIO_DMA_BUF_LEN,
    };

    esp_err_t err = i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
    if (err != ESP_OK) {
        DBG_PRINTF("[AUDIO] I2S driver install failed: %d\n", err);
        return false;
    }

    // ---- 引脚映射 ----
    // PDM 模式下 BCK 引脚不使用; WS 引脚输出 PDM 时钟
    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_PIN_NO_CHANGE,
        .ws_io_num = I2S_PDM_CLK,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_PDM_DATA,
    };

    err = i2s_set_pin(I2S_PORT, &pin_config);
    if (err != ESP_OK) {
        DBG_PRINTF("[AUDIO] I2S set pin failed: %d\n", err);
        i2s_driver_uninstall(I2S_PORT);
        return false;
    }

    g_initialized = true;
    DBG_PRINTF("[AUDIO] I2S PDM initialized @ %d Hz, %d-bit, %d ch\n",
               AUDIO_SAMPLE_RATE, AUDIO_BITS, AUDIO_CHANNELS);
    return true;
}

// ===== 录音会话管理 =====

void audio_start() {
    if (!g_initialized) return;
    reset_audio_buffer();
    i2s_zero_dma_buffer(I2S_PORT);
}

void audio_stop() {
    if (!g_initialized) return;
    i2s_zero_dma_buffer(I2S_PORT);
}

// ===== 数据采集 =====

uint32_t audio_read(uint8_t* buffer, uint32_t max_size) {
    if (!g_initialized || max_size < AUDIO_CHUNK_SIZE) return 0;

    size_t bytes_read = 0;
    esp_err_t err = i2s_read(I2S_PORT, buffer, AUDIO_CHUNK_SIZE,
                             &bytes_read, pdMS_TO_TICKS(10));
    if (err == ESP_OK) {
        g_i2s_err_count = 0;
        g_last_read_ok_ms = millis();
        return bytes_read;
    } else {
        g_i2s_err_count++;
        return 0;
    }
}

// 检查 I2S 健康状态, 如果连续失败超过阈值则尝试复位
void audio_check_health() {
    if (!g_initialized) return;
    if (g_i2s_err_count < I2S_ERR_THRESHOLD) return;

    DBG_PRINTF("[AUDIO] I2S %d consecutive errors, reinitializing...\n", g_i2s_err_count);
    i2s_driver_uninstall(I2S_PORT);
    g_initialized = false;
    g_i2s_err_count = 0;

    if (audio_init()) {
        DBG_PRINTF("[AUDIO] Reinitialization OK\n");
    } else {
        DBG_PRINTF("[AUDIO] Reinitialization FAILED\n");
    }
}

// ===== 主循环 Tick =====

void audio_process_tick() {
    if (!g_initialized) return;

    uint8_t chunk[AUDIO_CHUNK_SIZE];
    size_t bytes_read = 0;

    // 从 I2S DMA 读取 PCM 数据 (10ms 超时, 不阻塞主循环)
    esp_err_t err = i2s_read(I2S_PORT, chunk, AUDIO_CHUNK_SIZE,
                             &bytes_read, pdMS_TO_TICKS(10));
    if (err != ESP_OK || bytes_read == 0) return;

    // 1. 写入本地音频缓冲区 (作为备份 / 总大小统计)
    uint32_t space = audio_buffer_size - audio_buffer_pos;
    uint32_t to_copy = (bytes_read < space) ? bytes_read : space;
    if (to_copy > 0) {
        memcpy(audio_buffer + audio_buffer_pos, chunk, to_copy);
        audio_buffer_pos += to_copy;
    }

    // 2. 通过蓝牙实时发送音频块
    //    Bridge 端接收后积累到 audio_buffer 中
    send_frame(MSG_AUDIO_DATA, chunk, bytes_read);
}
