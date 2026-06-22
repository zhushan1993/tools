"""
M5STICK Bridge — 二进制帧编解码

帧格式:
  [Magic 2B: 0xCC55][Length 2B LE][Type 1B][Payload Length B]

所有多字节整数为小端序 (LE)。
"""

import struct
from typing import Optional
from .config import FRAME_MAGIC

HEADER_SIZE = 5  # Magic(2) + Length(2) + Type(1)


def encode_frame(msg_type: int, payload: bytes = b"") -> bytes:
    """编码一帧数据"""
    length = len(payload)
    header = struct.pack("<HHB", FRAME_MAGIC, length, msg_type)
    return header + payload


def decode_frame(data: bytes) -> Optional[tuple]:
    """
    解码帧数据。
    返回 (msg_type, payload) 或 None (数据不完整/无效)。
    注意: 如果 data 包含多帧，只解码第一帧。
    """
    if len(data) < HEADER_SIZE:
        return None

    magic, length, msg_type = struct.unpack_from("<HHB", data, 0)

    if magic != FRAME_MAGIC:
        return None  # 无效帧

    total_size = HEADER_SIZE + length
    if len(data) < total_size:
        return None  # 数据不完整

    payload = data[HEADER_SIZE:total_size]
    return msg_type, payload, total_size


class FrameParser:
    """
    流式帧解析器。
    从串口/蓝牙持续接收字节流，自动拼装完整帧。
    """

    def __init__(self):
        self._buffer = bytearray()
        self._expected_total = 0

    def feed(self, data: bytes) -> list[tuple]:
        """
        喂入新收到的字节数据。
        返回已解析出的完整帧列表: [(msg_type, payload), ...]
        """
        self._buffer.extend(data)
        frames = []

        while True:
            if len(self._buffer) < HEADER_SIZE:
                break

            magic, length, msg_type = struct.unpack_from("<HHB", self._buffer, 0)

            if magic != FRAME_MAGIC:
                # Magic 不匹配: 向前搜索直到找到匹配
                idx = self._buffer.find(b"\x55\xCC")  # 注意小端序
                if idx == -1:
                    idx = self._buffer.find(b"\xCC\x55")
                if idx == -1:
                    idx = len(self._buffer) - 1
                self._buffer = self._buffer[idx:] if idx < len(self._buffer) else bytearray()
                continue

            total = HEADER_SIZE + length
            if len(self._buffer) < total:
                break  # 等待更多数据

            payload = bytes(self._buffer[HEADER_SIZE:total])
            frames.append((msg_type, payload))

            # 移除已处理数据
            self._buffer = self._buffer[total:]

        return frames

    def reset(self):
        self._buffer.clear()
