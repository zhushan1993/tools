#!/bin/bash
# 为tools目录下的每个工具创建独立的虚拟环境
# 用法: ./setup_venvs.sh

set -e  # 遇到错误时退出

echo "开始为各个工具创建独立的虚拟环境..."
echo "======================================"

# 定义需要创建虚拟环境的工具目录及其requirements.txt路径
# 格式: "目录路径:requirements.txt路径"
TOOLS=(
    "markdown_to_pdf:requirements.txt"
    "resize_pdf:requirements.txt"
    "pdf_to_md/handwrite_pdf:requirements.txt"
    "pdf_to_md/scan_pdf_ocr:requirements.txt"
    "m4a_to_md:requirements.txt"
    "md_to_word:requirements.txt"
)

# 检查Python3是否可用
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装Python3"
    exit 1
fi

# 检查venv模块是否可用
python3 -c "import venv" 2>/dev/null || {
    echo "错误: Python3 venv模块不可用，请确保已安装python3-venv"
    exit 1
}

# 创建每个工具的虚拟环境
for tool_spec in "${TOOLS[@]}"; do
    IFS=':' read -r tool_dir req_file <<< "$tool_spec"

    if [ ! -d "$tool_dir" ]; then
        echo "跳过: 目录 $tool_dir 不存在"
        continue
    fi

    cd "$tool_dir" || {
        echo "错误: 无法进入目录 $tool_dir"
        exit 1
    }

    echo ""
    echo "处理工具: $tool_dir"
    echo "--------------------------------------"

    # 检查是否已有虚拟环境
    if [ -d ".venv" ]; then
        echo "  虚拟环境 .venv 已存在，跳过创建"
    else
        echo "  创建虚拟环境 .venv"
        python3 -m venv .venv
    fi

    # 激活虚拟环境并安装依赖
    if [ -f ".venv/bin/activate" ]; then
        echo "  安装依赖..."
        # 使用虚拟环境中的pip安装
        .venv/bin/pip install --upgrade pip

        if [ -f "$req_file" ]; then
            .venv/bin/pip install -r "$req_file"
        else
            echo "  警告: 未找到 $req_file，跳过依赖安装"
        fi

        echo "  依赖安装完成"
    else
        echo "  错误: 虚拟环境创建失败，.venv/bin/activate 不存在"
    fi

    cd - > /dev/null || exit 1
done

echo ""
echo "======================================"
echo "虚拟环境创建完成！"
echo ""
echo "使用说明:"
echo "1. 进入工具目录: cd tool_directory"
echo "2. 激活虚拟环境: source .venv/bin/activate"
echo "3. 运行工具: python your_tool.py"
echo "4. 退出虚拟环境: deactivate"
echo ""
echo "可选: 删除旧的统一虚拟环境"
echo "  rm -rf pdf_to_md/venv_old"
echo ""
echo "注意:"
echo "- merge_csv 工具只使用标准库，无需虚拟环境"
echo "- m4a_to_md 工具需要系统依赖（FFmpeg等）"
echo "- 某些工具可能需要系统依赖（如 tesseract-ocr, poppler-utils, ffmpeg）"
echo "  请参考各工具的 requirements.txt 中的说明安装系统依赖"