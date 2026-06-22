#!/usr/bin/env python3
"""
M5STICK Bridge Server — 主协调器

将 M5STICK 蓝牙设备与 Claude Code CLI 对接，实现：
1. 物理按键授权确认
2. 语音输入转文字

用法:
  python -m bridge.server                    # 直接运行 (自动启动 Claude)
  python -m bridge.server --no-claude        # 仅启动 M5STICK 通信测试
  python -m bridge.server --scan             # 扫描并选择蓝牙设备
"""

import sys
import json
import time
import struct
import logging
import argparse
import threading
from typing import Optional
from .config import (
    LOG_CONFIG, BT_CONFIG, CLAUDE_CONFIG, STT_CONFIG,
    MSG_BUTTON_PRESS, MSG_AUDIO_DATA, MSG_RECORDING_DONE,
    MSG_PING, MSG_PONG, MSG_DISPLAY_CONFIRM, MSG_DISPLAY_TEXT,
    MSG_SET_MODE, MSG_START_RECORDING, MSG_STOP_RECORDING,
)

logger = logging.getLogger("bridge")


class BridgeServer:
    """协调 M5STICK 和 Claude Code 的桥接服务。"""

    def __init__(self, with_claude=True):
        self.with_claude = with_claude
        self.running = False

        # 蓝牙 SPP 客户端 (Threading 模式)
        from .spp_client import SPPClient
        self.spp = SPPClient(
            port=BT_CONFIG["rfcomm_port"],
            on_frame=self._on_frame,
            on_connect=self._on_connect,
            on_disconnect=self._on_disconnect,
        )

        # 音频接收状态
        self.audio_buffer = bytearray()
        self.recording = False
        self.recording_start_time = 0.0

        # 授权状态
        self.current_req_id: Optional[str] = None
        self.current_tool_input: Optional[dict] = None
        self.pending_confirm = False
        self._confirm_lock = threading.Lock()
        self._confirm_timeout = CLAUDE_CONFIG.get("timeout_ms", 60000) / 1000.0
        self._confirm_start_time = 0.0

        # Claude IPC (使用同步包装)
        self.claude: Optional['SyncClaudeIPC'] = None

    def start(self):
        """启动桥接服务。"""
        logging.basicConfig(
            level=getattr(logging, LOG_CONFIG["level"]),
            format=LOG_CONFIG["format"],
        )
        logger.info("=" * 50)
        logger.info("M5STICK Bridge Server 启动")
        logger.info(f"  蓝牙设备: {BT_CONFIG['rfcomm_port']}")
        logger.info(f"  启动 Claude: {self.with_claude}")
        logger.info("=" * 50)

        self.running = True

        # 连接蓝牙 (含自动重连)
        if not self.spp.connect():
            logger.warning("蓝牙首次连接失败，将在后台重试...")

        # 启动 Claude IPC
        if self.with_claude:
            self._start_claude()

        # 主循环
        try:
            while self.running:
                self._tick()
                self._check_reconnect()
                time.sleep(0.05)  # 20fps
        except KeyboardInterrupt:
            logger.info("用户中断")
        finally:
            self.stop()

    def stop(self):
        """停止桥接服务。"""
        self.running = False
        if self.claude:
            self.claude.stop()
        self.spp.disconnect()
        logger.info("Bridge Server 已停止")

    def _tick(self):
        """主循环 tick，处理超时等。"""
        # 检查授权超时
        if self.pending_confirm:
            elapsed = time.time() - self._confirm_start_time
            if elapsed > self._confirm_timeout:
                logger.warning(f"授权超时 ({self._confirm_timeout}s)，自动拒绝")
                self._auto_deny()

        # 检查录音超时
        if self.recording:
            elapsed = time.time() - self.recording_start_time
            # 15s 超时由 M5STICK 侧处理，此处仅做后备

    _reconnect_retry_sec = 5  # 重试间隔
    _last_reconnect_attempt = 0.0

    def _check_reconnect(self):
        """如果蓝牙断开则自动重连。"""
        if self.spp.connected:
            return
        now = time.time()
        if now - self._last_reconnect_attempt < self._reconnect_retry_sec:
            return
        self._last_reconnect_attempt = now
        logger.info("蓝牙断开，尝试重连...")
        if self.spp.connect():
            logger.info("蓝牙重连成功")
            # 复位所有状态
            self.audio_buffer.clear()
            self.recording = False
            with self._confirm_lock:
                self.pending_confirm = False
                self.current_req_id = None
                self.current_tool_input = None

    # ===== Claude Code 管理 =====

    def _start_claude(self):
        """启动 Claude Code 子进程。"""
        from .claude_ipc import SyncClaudeIPC

        self.claude = SyncClaudeIPC()
        self.claude.on_permission_request = self._on_permission_request

        # 将用户命令行参数传递给 Claude
        claude_args = sys.argv[1:] if len(sys.argv) > 1 else []
        # 过滤掉我们自己认识的参数
        claude_args = [a for a in claude_args if a not in ("--no-claude", "--scan")]

        if self.claude.start(claude_args if claude_args else None):
            logger.info("Claude Code 已启动")
        else:
            logger.error("Claude Code 启动失败")

    def _on_permission_request(self, request):
        """收到 Claude Code 的授权请求。"""
        logger.info(f"授权请求: {request.tool_name} | {str(request.tool_input)[:100]}")

        with self._confirm_lock:
            self.current_req_id = request.request_id
            self.current_tool_input = request.tool_input
            self.pending_confirm = True
            self._confirm_start_time = time.time()

        # 发送到 M5STICK 显示
        cmd_text = json.dumps(request.tool_input.get("command", request.tool_input.get("text", "")), ensure_ascii=False)
        if cmd_text.startswith('"') and cmd_text.endswith('"'):
            cmd_text = cmd_text[1:-1]

        self.spp.send_confirm(
            tool=request.tool_name,
            cmd=cmd_text,
            req_id=request.request_id,
        )
        self.spp.send_mode(1)  # MODE_CONFIRM_PENDING

        # 如果 M5STICK 未连接，自动拒绝
        if not self.spp.connected:
            logger.warning("M5STICK 未连接，自动拒绝授权")
            self._auto_deny()

    def _auto_deny(self):
        """超时自动拒绝。"""
        with self._confirm_lock:
            if not self.pending_confirm:
                return
            req_id = self.current_req_id
            self.pending_confirm = False
            self.current_req_id = None
            self.current_tool_input = None

        if self.claude and req_id:
            self.claude.respond_permission(req_id, allow=False, message="Timeout")

    # ===== STT 管理 (Phase 3) =====

    def _start_stt(self):
        """初始化 STT 引擎 (延迟加载)。"""
        if hasattr(self, '_stt') and self._stt:
            return
        from .stt_engine import STTEngine
        self._stt = STTEngine()

    async def _transcribe_audio(self, audio_data: bytes):
        """将录音转文字 (在后台线程调用)。"""
        self._start_stt()
        result = await self._stt.transcribe(audio_data)
        if result and result.text:
            logger.info(f"STT 识别结果: {result.text}")
            if self.claude:
                self.claude.send_user_input(result.text)
        else:
            logger.warning("STT 未能识别出有效文本")

    # ===== 蓝牙事件回调 =====

    def _on_connect(self):
        logger.info("M5STICK 蓝牙已连接")
        self.spp.send_mode(0)  # IDLE
        self.spp.send_status("Claude Code Ready")

    def _on_disconnect(self):
        logger.warning("M5STICK 蓝牙已断开")
        # 自动拒绝未处理的授权请求
        if self.pending_confirm:
            self._auto_deny()

    def _on_frame(self, msg_type: int, payload: bytes):
        """收到来自 M5STICK 的一帧数据。"""
        try:
            if msg_type == MSG_BUTTON_PRESS:
                self._handle_button(payload)
            elif msg_type == MSG_AUDIO_DATA:
                self._handle_audio(payload)
            elif msg_type == MSG_RECORDING_DONE:
                self._handle_recording_done(payload)
            elif msg_type == MSG_START_RECORDING:
                self.audio_buffer.clear()
                self.recording = True
                self.recording_start_time = time.time()
                logger.info("M5STICK 开始录音")
            elif msg_type == MSG_PING:
                self.spp.send(MSG_PONG, payload)
            elif msg_type == MSG_PONG:
                pass
            else:
                logger.debug(f"未知帧类型: 0x{msg_type:02x}")
        except Exception as e:
            logger.error(f"处理帧异常: {e}", exc_info=True)

    def _handle_button(self, payload: bytes):
        """处理来自 M5STICK 的按键事件。"""
        if len(payload) < 1:
            return
        button = payload[0]

        if button == 0x00:  # A = 确认
            logger.info("M5STICK 按键: A (确认)")
            with self._confirm_lock:
                if not self.pending_confirm:
                    logger.warning("没有待处理的授权请求")
                    return
                req_id = self.current_req_id
                tool_input = self.current_tool_input
                self.pending_confirm = False
                self.current_req_id = None
                self.current_tool_input = None

            if self.claude and req_id:
                self.claude.respond_permission(req_id, allow=True,
                                                updated_input=tool_input)
                logger.info(f"已授权: {req_id}")

        elif button == 0x01:  # B = 拒绝
            logger.info("M5STICK 按键: B (拒绝)")
            with self._confirm_lock:
                if self.pending_confirm:
                    req_id = self.current_req_id
                    self.pending_confirm = False
                    self.current_req_id = None
                    self.current_tool_input = None
                else:
                    req_id = None

            if self.claude and req_id:
                self.claude.respond_permission(req_id, allow=False,
                                                message="User denied via M5STICK")
                logger.info(f"已拒绝: {req_id}")

    def _handle_audio(self, payload: bytes):
        """处理音频数据块。"""
        if self.recording:
            self.audio_buffer.extend(payload)

    def _handle_recording_done(self, payload: bytes):
        """录音完成。"""
        total_bytes = struct.unpack("<I", payload[:4])[0] if len(payload) >= 4 else len(self.audio_buffer)
        duration = total_bytes / (STT_CONFIG["sample_rate"] * 2)
        logger.info(f"录音完成: {total_bytes} 字节 ({duration:.1f} 秒)")

        self.recording = False
        self.spp.send_mode(2)  # PROCESSING

        if len(self.audio_buffer) > 100:  # 至少 50ms 音频
            # 在后台线程运行 STT
            audio_data = bytes(self.audio_buffer)
            self.audio_buffer.clear()

            import asyncio
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._transcribe_audio(audio_data))
                loop.close()
            except Exception as e:
                logger.error(f"STT 处理失败: {e}")
                self.spp.send_status("识别失败")
        else:
            logger.warning("录音数据过短，跳过识别")
            self.spp.send_status("语音过短")

        self.spp.send_mode(0)  # 回到 IDLE


def main():
    parser = argparse.ArgumentParser(description="M5STICK Bridge Server")
    parser.add_argument("--no-claude", action="store_true",
                        help="不启动 Claude Code，仅测试 M5STICK 通信")
    parser.add_argument("--scan", action="store_true",
                        help="扫描蓝牙设备")
    args = parser.parse_args()

    if args.scan:
        print("扫描蓝牙设备...")
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            print(f"发现 {len(ports)} 个串口设备:")
            for p in ports:
                print(f"  {p.device}: {p.description}")
        except Exception as e:
            print(f"扫描失败: {e}")
        return

    server = BridgeServer(with_claude=not args.no_claude)
    server.start()


if __name__ == "__main__":
    main()
