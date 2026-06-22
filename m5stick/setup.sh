#!/usr/bin/env bash
#
# M5STICK Claude Code 便携化终端 — 环境搭建脚本
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BRIDGE_DIR="$SCRIPT_DIR/bridge"
FIRMWARE_DIR="$SCRIPT_DIR/firmware"
VENV_DIR="$BRIDGE_DIR/venv"
MODEL_DIR="$SCRIPT_DIR/../m4a_to_md/models/vosk"

echo "====================================="
echo " M5STICK Claude Code 终端 — 环境搭建"
echo "====================================="

# 1. 创建 venv 并安装 Python 依赖
echo ""
echo "[1/4] 安装 Python 依赖..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$BRIDGE_DIR/requirements.txt" -q
echo "  Python 依赖安装完成"

# 2. 安装 PlatformIO (如果未安装)
echo ""
echo "[2/4] 检查 PlatformIO..."
if ! command -v platformio &> /dev/null && ! "$VENV_DIR/bin/platformio" --version &>/dev/null; then
    echo "  正在安装 PlatformIO..."
    "$VENV_DIR/bin/pip" install platformio -q
    export PATH="$VENV_DIR/bin:$PATH"
fi
echo "  PlatformIO 就绪"

# 3. 下载 Vosk 中文模型（如果不存在）
echo ""
echo "[3/4] 检查 Vosk 中文模型..."
MODEL_PATH="$MODEL_DIR/vosk-model-small-zh-cn-0.22"
if [ ! -d "$MODEL_PATH" ]; then
    echo "  未找到中文模型，正在下载 (42MB)..."
    mkdir -p "$MODEL_DIR"
    cd "$MODEL_DIR"
    wget -q --show-progress \
        "https://alphacephei.com/vosk/models/vosk-model-small-zh-cn-0.22.zip" \
        -O model.zip
    unzip -q model.zip
    rm model.zip
    cd "$SCRIPT_DIR"
    echo "  模型下载完成: $MODEL_PATH"
else
    echo "  模型已存在: $MODEL_PATH"
fi

# 4. 编译固件
echo ""
echo "[4/4] 编译固件..."
cd "$FIRMWARE_DIR"
"$VENV_DIR/bin/platformio" run
cd "$SCRIPT_DIR"

echo ""
echo "====================================="
echo " 环境搭建完成!"
echo ""
echo "下一步:"
echo "  1. 刷入固件: cd firmware && $VENV_DIR/bin/platformio run -t upload"
echo "  2. 配对蓝牙: 在电脑蓝牙设置中搜索 'M5Stick-Claude' 并配对"
echo "  3. 启动 Bridge: $VENV_DIR/bin/python -m bridge.server"
echo "====================================="
