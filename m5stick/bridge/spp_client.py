"""
M5STICK Bridge — 蓝牙 SPP 客户端

通过 /dev/rfcomm0 (Linux) 或 COM 口 (Windows) 连接 M5STICK。
使用 pyserial 进行读写。
"""

import serial
import serial.tools.list_ports
import logging
import time
from typing import Optional, Callable
from threading import Thread, Event
from .config import BT_CONFIG
from .protocol import encode_frame, FrameParser

logger = logging.getLogger(__name__)


class SPPClient:
    """蓝牙 SPP 客户端，管理与 M5STICK 的串口连接。"""

    def __init__(
        self,
        port: str = None,
        baudrate: int = None,
        on_frame: Callable = None,
        on_connect: Callable = None,
        on_disconnect: Callable = None,
    ):
        self.port = port or BT_CONFIG["rfcomm_port"]
        self.baudrate = baudrate or BT_CONFIG["baudrate"]
        self.timeout = BT_CONFIG["timeout"]
        self.on_frame = on_frame
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect

        self._serial: Optional[serial.Serial] = None
        self._running = False
        self._reader_thread: Optional[Thread] = None
        self._stop_event = Event()
        self._parser = FrameParser()

    @property
    def connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def connect(self) -> bool:
        """连接到 M5STICK（阻塞）。返回是否成功。"""
        try:
            if self.port == "AUTO":
                self.port = self._auto_detect_port()
                if not self.port:
                    logger.error("未找到 M5STICK 蓝牙串口设备")
                    return False

            logger.info(f"正在连接 {self.port} @ {self.baudrate} baud...")
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=1,
            )
            time.sleep(2)  # 等待设备就绪
            logger.info(f"蓝牙 SPP 已连接: {self.port}")

            if self.on_connect:
                self.on_connect()

            self._start_reader()
            return True

        except serial.SerialException as e:
            logger.error(f"连接失败: {e}")
            self._serial = None
            return False

    def disconnect(self):
        """断开连接。"""
        self._stop_reader()
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception as e:
                logger.warning(f"关闭串口异常: {e}")
            logger.info("蓝牙 SPP 已断开")
            if self.on_disconnect:
                self.on_disconnect()
        self._serial = None

    def send(self, msg_type: int, payload: bytes = b"") -> bool:
        """发送一帧数据到 M5STICK。"""
        if not self.connected:
            logger.warning("未连接，无法发送")
            return False
        try:
            frame = encode_frame(msg_type, payload)
            self._serial.write(frame)
            self._serial.flush()
            return True
        except serial.SerialTimeoutException:
            logger.error("发送超时")
            return False
        except serial.SerialException as e:
            logger.error(f"发送异常: {e}")
            self.disconnect()
            return False

    def send_text(self, text: str) -> bool:
        """快捷发送 DISPLAY_TEXT 帧。"""
        from .config import MSG_DISPLAY_TEXT
        return self.send(MSG_DISPLAY_TEXT, text.encode("utf-8"))

    def send_confirm(self, tool: str, cmd: str, req_id: str) -> bool:
        """快捷发送 DISPLAY_CONFIRM 帧。"""
        from .config import MSG_DISPLAY_CONFIRM
        import json
        payload = json.dumps({
            "tool": tool,
            "cmd": cmd,
            "id": req_id,
        }, ensure_ascii=False).encode("utf-8")
        return self.send(MSG_DISPLAY_CONFIRM, payload)

    def send_mode(self, mode: int) -> bool:
        """快捷发送 SET_MODE 帧。"""
        from .config import MSG_SET_MODE
        return self.send(MSG_SET_MODE, bytes([mode]))

    def send_status(self, text: str) -> bool:
        """快捷发送 SHOW_STATUS 帧。"""
        from .config import MSG_SHOW_STATUS
        return self.send(MSG_SHOW_STATUS, text.encode("utf-8"))

    def _auto_detect_port(self) -> Optional[str]:
        """自动检测 M5STICK 蓝牙串口设备。"""
        ports = serial.tools.list_ports.comports()
        for p in ports:
            # 常见的蓝牙串口描述
            if any(kw in (p.description or "").lower() for kw in
                   ["m5stick", "bluetooth", "rfcomm", "serial"]):
                logger.info(f"自动检测到设备: {p.device} ({p.description})")
                return p.device
            # 也匹配 Linux rfcomm 设备
            if "rfcomm" in p.device:
                logger.info(f"自动检测到蓝牙串口: {p.device}")
                return p.device
        return None

    def _start_reader(self):
        """启动读取线程。"""
        self._stop_event.clear()
        self._running = True
        self._reader_thread = Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

    def _stop_reader(self):
        """停止读取线程。"""
        self._running = False
        self._stop_event.set()
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=2)
        self._reader_thread = None

    def _read_loop(self):
        """后台读取线程：持续读取串口数据并解析帧。"""
        while self._running and not self._stop_event.is_set():
            if not self.connected:
                break
            try:
                if self._serial.in_waiting > 0:
                    data = self._serial.read(self._serial.in_waiting)
                    frames = self._parser.feed(data)
                    for msg_type, payload in frames:
                        if self.on_frame:
                            try:
                                self.on_frame(msg_type, payload)
                            except Exception as e:
                                logger.error(f"帧处理异常: {e}")
                else:
                    self._stop_event.wait(0.01)  # 10ms 轮询间隔
            except serial.SerialException as e:
                logger.error(f"读取异常: {e}")
                break
            except Exception as e:
                logger.error(f"读取线程异常: {e}")
                break

        # 连接断开
        if self.connected:
            try:
                self._serial.close()
            except Exception:
                pass
        logger.info("读取线程已停止")
        if self.on_disconnect:
            self.on_disconnect()
