#!/bin/bash
# PDF手写体识别运行脚本
# 用法: ./run.sh input.pdf output.md [选项]

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# 使用父目录中的虚拟环境
VENV_DIR="$DIR/../venv"

# 检查虚拟环境是否存在
if [ ! -d "$VENV_DIR" ]; then
    echo "错误: 虚拟环境不存在，请先运行 setup.sh 或手动创建虚拟环境"
    echo "虚拟环境预期路径: $VENV_DIR"
    exit 1
fi

# 检查Python脚本是否存在
if [ ! -f "$DIR/handwrite_pdf_to_md.py" ]; then
    echo "错误: Python脚本不存在: $DIR/handwrite_pdf_to_md.py"
    exit 1
fi

# 使用虚拟环境中的Python运行脚本
"$VENV_DIR/bin/python" "$DIR/handwrite_pdf_to_md.py" "$@"