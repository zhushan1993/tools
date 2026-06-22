#!/usr/bin/env python3
"""
集成测试 — 模拟 M5STICK 与 Bridge Server 的通信

无需实际硬件即可验证协议层正确性。
"""

import sys
import os
import time
import threading
import struct
from typing import Optional

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridge.protocol import encode_frame, decode_frame, FrameParser
from bridge.config import (
    MSG_DISPLAY_TEXT, MSG_DISPLAY_CONFIRM, MSG_SET_MODE,
    MSG_BUTTON_PRESS, MSG_AUDIO_DATA, MSG_RECORDING_DONE,
    MSG_START_RECORDING, MSG_STOP_RECORDING,
    MSG_PING, MSG_PONG, FRAME_MAGIC,
)


class MockSPP:
    """模拟蓝牙 SPP 连接（内存管道）。"""

    def __init__(self):
        self._bridge_to_device = bytearray()
        self._device_to_bridge = bytearray()
        self._lock = threading.Lock()

    def bridge_write(self, data: bytes):
        with self._lock:
            self._bridge_to_device.extend(data)

    def device_write(self, data: bytes):
        with self._lock:
            self._device_to_bridge.extend(data)

    def bridge_read_all(self) -> bytes:
        with self._lock:
            data = bytes(self._device_to_bridge)
            self._device_to_bridge.clear()
            return data

    def device_read_all(self) -> bytes:
        with self._lock:
            data = bytes(self._bridge_to_device)
            self._bridge_to_device.clear()
            return data


class MockM5STICK:
    """模拟 M5STICK 固件行为。"""

    def __init__(self, spp: MockSPP):
        self.spp = spp
        self.mode = 0  # IDLE
        self.parser = FrameParser()
        self.displayed_text = ""
        self.last_confirm = None
        self.button_pressed = None
        self.recording_active = False
        self.audio_data = bytearray()

    def tick(self):
        """处理一帧传入数据。"""
        data = self.spp.device_read_all()
        if not data:
            return
        frames = self.parser.feed(data)
        for msg_type, payload in frames:
            self._handle_frame(msg_type, payload)

    def _handle_frame(self, msg_type: int, payload: bytes):
        if msg_type == MSG_DISPLAY_TEXT:
            self.displayed_text = payload.decode("utf-8", errors="replace")
            print(f"  [M5] 显示文本: {self.displayed_text}")

        elif msg_type == MSG_DISPLAY_CONFIRM:
            self.last_confirm = payload.decode("utf-8", errors="replace")
            self.mode = 1  # CONFIRM_PENDING
            print(f"  [M5] 收到确认请求: {self.last_confirm[:80]}...")

        elif msg_type == MSG_SET_MODE:
            self.mode = payload[0] if payload else 0
            print(f"  [M5] 模式切换: {self.mode}")

        elif msg_type == MSG_START_RECORDING:
            self.recording_active = True
            self.audio_data.clear()
            print(f"  [M5] 开始录音 (最长 {payload[0] if payload else 15}s)")

        elif msg_type == MSG_STOP_RECORDING:
            self.recording_active = False
            self.spp.device_write(
                encode_frame(MSG_RECORDING_DONE, struct.pack("<I", len(self.audio_data)))
            )
            print(f"  [M5] 停止录音 (共 {len(self.audio_data)} 字节)")

        elif msg_type == MSG_PING:
            self.spp.device_write(encode_frame(MSG_PONG, payload))
            print(f"  [M5] PING -> PONG")

    def press_button(self, button_id: int):
        """模拟按键。"""
        self.spp.device_write(encode_frame(MSG_BUTTON_PRESS, bytes([button_id])))
        if button_id == 0:
            print(f"  [M5] 按键 A (确认)")
        else:
            print(f"  [M5] 按键 B (拒绝)")

    def send_audio_chunk(self, chunk: bytes):
        """模拟发送音频块。"""
        self.spp.device_write(encode_frame(MSG_AUDIO_DATA, chunk))
        self.audio_data.extend(chunk)

    def send_recording_done(self):
        """模拟录音完成。"""
        self.spp.device_write(
            encode_frame(MSG_RECORDING_DONE, struct.pack("<I", len(self.audio_data)))
        )
        print(f"  [M5] 录音完成 (共 {len(self.audio_data)} 字节)")


def test_basic_communication():
    """测试 1: 基础通信 — Bridge 发 DISPLAY_TEXT，M5 收到。"""
    print("\n" + "=" * 50)
    print("测试 1: 基础通信 (DISPLAY_TEXT)")
    print("=" * 50)

    spp = MockSPP()
    m5 = MockM5STICK(spp)
    bridge_parser = FrameParser()

    # Bridge 发送文本
    spp.bridge_write(encode_frame(MSG_DISPLAY_TEXT, b"Claude Code Ready"))
    m5.tick()
    assert m5.displayed_text == "Claude Code Ready", f"Got: {m5.displayed_text}"
    print("  ✅ Bridge 发送的文本被 M5 正确接收")
    print("  ✅ 测试通过")


def test_confirm_flow():
    """测试 2: 授权确认流程。"""
    print("\n" + "=" * 50)
    print("测试 2: 授权确认流程")
    print("=" * 50)

    spp = MockSPP()
    m5 = MockM5STICK(spp)
    bridge_parser = FrameParser()

    # Bridge 发送确认请求
    payload = b'{"tool":"Bash","cmd":"rm -rf /tmp/test","id":"req_001"}'
    spp.bridge_write(encode_frame(MSG_DISPLAY_CONFIRM, payload))
    m5.tick()
    assert m5.mode == 1, f"模式应为 CONFIRM_PENDING, 实际: {m5.mode}"
    print("  ✅ M5 进入确认模式")

    # M5 按 A 确认
    m5.press_button(0)
    frames = bridge_parser.feed(spp.bridge_read_all())
    assert len(frames) == 1, f"应收到 1 帧, 实际: {len(frames)}"
    msg_type, payload = frames[0]
    assert msg_type == MSG_BUTTON_PRESS, f"类型应为 BUTTON_PRESS, 实际: 0x{msg_type:02x}"
    assert payload[0] == 0, f"按键应为 A(0), 实际: {payload[0]}"
    print("  ✅ Bridge 正确收到确认按键")

    # M5 按 B 拒绝
    m5.press_button(1)
    frames = bridge_parser.feed(spp.bridge_read_all())
    msg_type, payload = frames[0]
    assert payload[0] == 1, f"按键应为 B(1), 实际: {payload[0]}"
    print("  ✅ Bridge 正确收到拒绝按键")

    print("  ✅ 测试通过")


def test_audio_stream():
    """测试 3: 音频流传输。"""
    print("\n" + "=" * 50)
    print("测试 3: 音频流传输")
    print("=" * 50)

    spp = MockSPP()
    m5 = MockM5STICK(spp)
    bridge_parser = FrameParser()

    # Bridge 开始录音
    spp.bridge_write(encode_frame(MSG_START_RECORDING, b'\x0f'))
    m5.tick()
    assert m5.recording_active, "M5 应进入录音模式"
    print("  ✅ M5 开始录音")

    # M5 发送音频块
    chunk = b'\x00\x01\x02\x03' * 128  # 512 字节
    m5.send_audio_chunk(chunk)
    frames = bridge_parser.feed(spp.bridge_read_all())
    assert len(frames) == 1
    msg_type, payload = frames[0]
    assert msg_type == MSG_AUDIO_DATA, f"应为 AUDIO_DATA, 实际: 0x{msg_type:02x}"
    assert len(payload) == 512, f"音频块应为 512 字节, 实际: {len(payload)}"
    print("  ✅ Bridge 正确收到音频块")

    # 发送多个音频块然后完成
    for i in range(5):
        m5.send_audio_chunk(chunk)
    m5.send_recording_done()

    frames = bridge_parser.feed(spp.bridge_read_all())
    audio_chunks = sum(1 for t, _ in frames if t == MSG_AUDIO_DATA)
    done_frames = sum(1 for t, _ in frames if t == MSG_RECORDING_DONE)
    assert audio_chunks == 5, f"应有 5 个音频块, 实际: {audio_chunks}"
    assert done_frames == 1, f"应有 1 个完成帧, 实际: {done_frames}"
    print(f"  ✅ 共收到 {audio_chunks} 个音频块 + 1 个完成通知")

    print("  ✅ 测试通过")


def test_heartbeat():
    """测试 4: 心跳 PING/PONG。"""
    print("\n" + "=" * 50)
    print("测试 4: 心跳 PING/PONG")
    print("=" * 50)

    spp = MockSPP()
    m5 = MockM5STICK(spp)
    bridge_parser = FrameParser()

    # Bridge 发送 PING
    spp.bridge_write(encode_frame(MSG_PING, struct.pack("<I", 12345)))
    m5.tick()

    frames = bridge_parser.feed(spp.bridge_read_all())
    assert len(frames) == 1, f"应有 1 个 PONG 回复, 实际: {len(frames)}"
    msg_type, payload = frames[0]
    assert msg_type == MSG_PONG, f"应为 PONG, 实际: 0x{msg_type:02x}"
    ts = struct.unpack("<I", payload)[0]
    assert ts == 12345, f"时间戳应回显, 实际: {ts}"
    print("  ✅ PING/PONG 正确")

    print("  ✅ 测试通过")


def test_multiple_frames():
    """测试 5: 多帧粘包处理。"""
    print("\n" + "=" * 50)
    print("测试 5: 多帧粘包处理")
    print("=" * 50)

    spp = MockSPP()
    m5 = MockM5STICK(spp)
    bridge_parser = FrameParser()

    # 一次发送多个帧
    batch = (
        encode_frame(MSG_DISPLAY_TEXT, b"Line 1") +
        encode_frame(MSG_SET_MODE, b'\x02') +
        encode_frame(MSG_DISPLAY_TEXT, b"Line 2")
    )
    spp.bridge_write(batch)
    m5.tick()

    # 验证 M5 处理了所有帧
    assert m5.displayed_text == "Line 2", f"最后显示的文本不对: {m5.displayed_text}"
    assert m5.mode == 2, f"模式应为 2, 实际: {m5.mode}"
    print("  ✅ M5 正确处理粘包多帧")

    print("  ✅ 测试通过")


def test_garbage_recovery():
    """测试 6: 垃圾数据恢复。"""
    print("\n" + "=" * 50)
    print("测试 6: 垃圾数据恢复")
    print("=" * 50)

    parser = FrameParser()

    # 先喂垃圾数据，再喂有效帧
    garbage = b'\x00\x00\x00\x00\x00\xde\xad\xbe\xef'
    valid = encode_frame(MSG_DISPLAY_TEXT, b"recovered")

    frames = parser.feed(garbage + valid)
    assert len(frames) == 1, f"应有 1 个恢复帧, 实际: {len(frames)}"
    msg_type, payload = frames[0]
    assert msg_type == MSG_DISPLAY_TEXT, f"类型错误: 0x{msg_type:02x}"
    assert payload == b"recovered"
    print("  ✅ 垃圾数据后正确恢复")

    print("  ✅ 测试通过")


if __name__ == "__main__":
    print("=" * 50)
    print("M5STICK Bridge 集成测试套件")
    print("=" * 50)

    tests = [
        test_basic_communication,
        test_confirm_flow,
        test_audio_stream,
        test_heartbeat,
        test_multiple_frames,
        test_garbage_recovery,
    ]

    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 50)
    print(f"测试完成: {passed}/{len(tests)} 通过")
    print("=" * 50)

    sys.exit(0 if passed == len(tests) else 1)
