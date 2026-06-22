#include "protocol.h"
#include <esp_heap_caps.h>

Stream* comm_stream = nullptr;

void set_comm_stream(Stream* stream) {
    comm_stream = stream;
}

uint8_t* audio_buffer = NULL;
const uint32_t audio_buffer_size = AUDIO_BUFFER_SIZE;
volatile uint32_t audio_buffer_pos = 0;

void reset_audio_buffer() {
    // 分配 PSRAM (SPIRAM) 以节省内部 DRAM
    if (!audio_buffer) {
        audio_buffer = (uint8_t*)heap_caps_malloc(audio_buffer_size, MALLOC_CAP_SPIRAM);
        if (!audio_buffer) {
            // Fallback: 分配内部 DRAM
            audio_buffer = (uint8_t*)malloc(audio_buffer_size);
        }
    }
    if (audio_buffer) {
        memset(audio_buffer, 0, audio_buffer_size);
    }
    audio_buffer_pos = 0;
}

bool send_frame(uint8_t type, const uint8_t* payload, uint16_t length) {
    if (!comm_stream) return false;

    FrameHeader header;
    header.magic  = FRAME_MAGIC;
    header.length = length;
    header.type   = type;

    size_t written = comm_stream->write((uint8_t*)&header, sizeof(header));
    if (written != sizeof(header)) return false;

    if (length > 0 && payload != nullptr) {
        written = comm_stream->write(payload, length);
        if (written != length) return false;
    }
    return true;
}

bool send_frame(uint8_t type) {
    return send_frame(type, nullptr, 0);
}

// 非阻塞读取一帧
// 返回 true 当且仅当读完一整个帧
// 如果部分帧停留时间超过 READ_TIMEOUT_MS, 自动丢弃并重置
bool read_frame(uint8_t* out_type, uint8_t* out_payload, uint16_t* out_length, uint16_t max_len) {
    static uint8_t frame_buffer[512];  // 帧接收缓冲
    static uint16_t bytes_read = 0;
    static bool header_done = false;
    static uint16_t expected_payload = 0;
    static uint8_t frame_type = 0;
    static unsigned long last_byte_ms = 0;

    if (!comm_stream) return false;

    // 部分帧超时检测: 5 秒内未收到新字节则丢弃
    if (header_done && (millis() - last_byte_ms > 5000)) {
        bytes_read = 0;
        header_done = false;
        comm_stream->flush();
    }

    while (comm_stream->available() > 0) {
        uint8_t b = comm_stream->read();
        last_byte_ms = millis();

        if (!header_done) {
            if (bytes_read < sizeof(FrameHeader)) {
                frame_buffer[bytes_read++] = b;
                if (bytes_read == sizeof(FrameHeader)) {
                    // 解析头部
                    FrameHeader* hdr = (FrameHeader*)frame_buffer;
                    if (hdr->magic != FRAME_MAGIC) {
                        // 无效 magic, 重新同步
                        bytes_read = 0;
                        comm_stream->flush();
                        return false;
                    }
                    expected_payload = hdr->length;
                    frame_type = hdr->type;

                    if (expected_payload == 0) {
                        // 无 payload, 直接完成
                        *out_type = frame_type;
                        *out_length = 0;
                        bytes_read = 0;
                        header_done = false;
                        return true;
                    }
                    header_done = true;
                    bytes_read = 0;  // 重置为 payload 做准备
                }
            }
        } else {
            // 读取 payload
            frame_buffer[bytes_read++] = b;
            if (bytes_read >= expected_payload) {
                // 完整帧完成
                uint16_t copy_len = min(expected_payload, max_len);
                memcpy(out_payload, frame_buffer, copy_len);
                *out_type = frame_type;
                *out_length = copy_len;
                bytes_read = 0;
                header_done = false;
                return true;
            }
        }
    }
    return false;  // 数据不完整
}
