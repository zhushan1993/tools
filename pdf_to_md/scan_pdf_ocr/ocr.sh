#!/bin/bash
# PDF OCR 快速启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/pdf_ocr_tool.py"

# 检查依赖
check_dependencies() {
    local missing=0
    
    if ! command -v tesseract &> /dev/null; then
        echo "❌ 未找到 tesseract，请安装：apt-get install -y tesseract-ocr tesseract-ocr-chi-sim"
        missing=1
    fi
    
    if ! command -v pdftoppm &> /dev/null; then
        echo "❌ 未找到 pdftoppm，请安装：apt-get install -y poppler-utils"
        missing=1
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ 未找到 python3"
        missing=1
    fi
    
    if [ $missing -eq 1 ]; then
        exit 1
    fi
    
    echo "✓ 依赖检查通过"
}

# 显示帮助
show_help() {
    echo "PDF OCR 工具 - 快速启动脚本"
    echo ""
    echo "用法：$0 [选项] <PDF 文件或目录>"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -d, --dpi      设置 DPI（默认 300）"
    echo "  -l, --lang     设置语言（默认 chi_sim+eng）"
    echo "  -o, --output   设置输出目录"
    echo "  --batch        批量模式"
    echo ""
    echo "示例:"
    echo "  $0 document.pdf"
    echo "  $0 -d 400 document.pdf"
    echo "  $0 --batch /path/to/pdfs/"
}

# 主程序
main() {
    local dpi=300
    local lang="chi_sim+eng"
    local output_dir=""
    local batch_mode=false
    local input=""
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -d|--dpi)
                dpi="$2"
                shift 2
                ;;
            -l|--lang)
                lang="$2"
                shift 2
                ;;
            -o|--output)
                output_dir="$2"
                shift 2
                ;;
            --batch)
                batch_mode=true
                shift
                ;;
            -*)
                echo "未知选项：$1"
                show_help
                exit 1
                ;;
            *)
                input="$1"
                shift
                ;;
        esac
    done
    
    if [ -z "$input" ]; then
        echo "❌ 请指定输入文件"
        show_help
        exit 1
    fi
    
    # 检查依赖
    check_dependencies
    
    # 执行 OCR
    if [ "$batch_mode" = true ] || [ -d "$input" ]; then
        echo "批量模式：处理目录 $input"
        python3 "$PYTHON_SCRIPT" -i "$input"/*.pdf -o "output_" --batch --dpi $dpi --lang $lang
    else
        echo "处理文件：$input"
        python3 "$PYTHON_SCRIPT" -i "$input" -o "${input%.pdf}.md" --dpi $dpi --lang $lang
    fi
}

main "$@"
