# M5STICK Claude Code 便携化编程终端

将 M5STICK 变为物理 I/O 设备，通过蓝牙连接电脑，为 Claude Code 提供**物理按键确认**和**语音输入**功能。

## 功能

- **物理授权确认** — Claude Code 执行操作时，M5STICK 显示命令详情，按 A/B 键确认或拒绝
- **语音输入** — 按住 B 键说话，录音转文字后自动发送给 Claude Code
- **无线蓝牙** — 经典蓝牙 SPP 连接，不受线缆束缚

## 快速开始

```bash
# 1. 环境搭建
./setup.sh

# 2. 刷入固件
cd firmware && ../bridge/venv/bin/platformio run -t upload

# 3. 蓝牙配对 (电脑端配对 M5Stick-Claude)
# Linux 绑定 rfcomm:
sudo rfcomm bind /dev/rfcomm0 <M5STICK_BT_MAC>

# 4. 启动 Bridge
cd .. && bridge/venv/bin/python -m bridge.server
```

## 项目结构

```
m5stick/
├── bridge/              # Python 桥接服务 (运行在电脑上)
│   ├── __init__.py
│   ├── server.py        # 主协调器
│   ├── protocol.py      # 二进制帧编解码
│   ├── spp_client.py    # 蓝牙 SPP 客户端
│   ├── claude_ipc.py    # Claude Code IPC (control_request 协议)
│   ├── stt_engine.py    # 语音识别引擎 (Vosk / Whisper)
│   └── config.py        # 配置与常量
├── firmware/            # M5STICK 固件 (Arduino C++)
│   ├── platformio.ini
│   └── src/
│       ├── main.cpp     # 主程序/状态机
│       ├── config.h     # 引脚定义 & 协议常量
│       ├── protocol.h/cpp   # 帧编解码 & 音频缓冲
│       ├── display.h/cpp    # 屏幕界面
│       ├── audio.h/cpp      # I2S PDM 麦克风驱动
│       ├── buttons.h/cpp    # 按键事件 (短按/长按)
│       └── led.h/cpp        # RGB LED 控制
└── docs/
    ├── hardware-setup.md    # 硬件配置
    └── usage.md             # 使用说明
```

## 实现阶段

- **Phase 0** ✅ 环境搭建 + 基础固件
- **Phase 1** ✅ 蓝牙 SPP 通信层
- **Phase 2** ✅ 授权确认流程 (含代码重构: display/buttons/led 拆分独立模块)
- **Phase 3** ✅ 语音输入 (I2S PDM 麦克风驱动 + 实时音频流 + Vosk/Whisper 双引擎)
- **Phase 4** ⏳ 稳定性打磨 (重连优化 / 错误处理 / LED 指示灯完善)

## 协议

M5STICK <-> Bridge 通过经典蓝牙 SPP 传输自定义二进制帧:

```
[Magic 2B: 0xCC55][Length 2B LE][Type 1B][Payload]
```

详见 [protocol.py](bridge/protocol.py) 和 [config.h](firmware/src/config.h)。
