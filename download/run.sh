#!/bin/bash
# Hue 数据下载工具
# 用法: ./run.sh <sql_file> [-o output.csv]
# 环境变量: HUE_USER, HUE_PASSWORD

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$DIR/../../work/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "错误: 虚拟环境不存在: $VENV_DIR"
    exit 1
fi

"$VENV_DIR/bin/python" "$DIR/hue_download.py" "$@"
