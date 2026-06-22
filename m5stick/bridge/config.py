"""
M5STICK Bridge Server — 配置文件
"""

from pathlib import Path

# 项目根目录
BRIDGE_ROOT = Path(__file__).parent

# ===== 蓝牙 SPP 配置 =====
BT_CONFIG = {
    "device_name": "M5Stick-Claude",        # M5STICK 蓝牙设备名
    "rfcomm_port": "/dev/ttyUSB0",          # USB 串口 (USB_MODE) 或 /dev/rfcomm0 (蓝牙)
    "baudrate": 115200,                     # 串口波特率
    "timeout": 0.05,                        # 读取超时 (秒)
    "auto_reconnect": True,                 # 自动重连
    "reconnect_interval": 5,                # 重连间隔 (秒)
    "scan_on_start": True,                  # 启动时扫描蓝牙设备
}

# ===== Claude Code 配置 =====
CLAUDE_CONFIG = {
    "binary": "claude",                     # claude 可执行文件路径
    "timeout_ms": 60000,                    # 授权超时 (ms)
    "extra_args": [],                       # 额外 CLI 参数
}

# ===== STT 引擎配置 =====
STT_CONFIG = {
    "engine": "vosk",                       # vosk 或 whisper
    "sample_rate": 16000,
    "language": "zh-CN",
    # Vosk 配置
    "vosk": {
        "model_dir": BRIDGE_ROOT.parent.parent / "m4a_to_md" / "models" / "vosk",
        "model_name": "vosk-model-small-zh-cn-0.22",
        "model_url": "https://alphacephei.com/vosk/models/vosk-model-small-zh-cn-0.22.zip",
    },
    # Whisper 配置
    "whisper": {
        "model_size": "tiny",               # tiny, base, small
        "device": "cpu",
    },
}

# ===== 日志配置 =====
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    "file": BRIDGE_ROOT / "logs" / "bridge.log",
    "max_mb": 10,
    "backup_count": 3,
}

# 创建日志目录
LOG_CONFIG["file"].parent.mkdir(parents=True, exist_ok=True)

# ===== 协议帧类型常量 =====
# Bridge -> M5
MSG_DISPLAY_TEXT = 0x01
MSG_DISPLAY_CONFIRM = 0x02
MSG_SET_MODE = 0x03
MSG_START_RECORDING = 0x04
MSG_STOP_RECORDING = 0x05
MSG_SHOW_STATUS = 0x06

# M5 -> Bridge
MSG_BUTTON_PRESS = 0x10
MSG_AUDIO_DATA = 0x11
MSG_RECORDING_DONE = 0x12

# 双向
MSG_PING = 0x20
MSG_PONG = 0x21

# 帧 Magic
FRAME_MAGIC = 0xCC55
