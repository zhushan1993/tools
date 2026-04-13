#!/usr/bin/env python3
"""
简单的PDF手写体转Markdown工具
用法: python simple_pdf_to_md.py input.pdf output.md
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

def check_dependencies():
    """检查必要的依赖"""
    missing = []

    try:
        from pdf2image import convert_from_path
    except ImportError:
        missing.append("pdf2image")

    try:
        from paddleocr import PaddleOCR
    except ImportError:
        missing.append("paddleocr")

    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        # pytesseract是可选的，不加入missing
        pass

    return missing

def main():
    parser = argparse.ArgumentParser(description='PDF转Markdown工具')
    parser.add_argument('input_pdf', help='输入PDF文件路径')
    parser.add_argument('output_md', help='输出Markdown文件路径')
    parser.add_argument('--engine', choices=['paddle', 'tesseract'], default='paddle',
                       help='OCR引擎: paddle (推荐) 或 tesseract (默认: paddle)')
    parser.add_argument('--dpi', type=int, default=300,
                       help='图像DPI (默认: 300)')

    args = parser.parse_args()

    # 检查文件
    input_path = Path(args.input_pdf)
    output_path = Path(args.output_md)

    if not input_path.exists():
        print(f"错误: 输入文件不存在: {input_path}")
        sys.exit(1)

    # 检查依赖
    missing = check_dependencies()
    if 'pdf2image' in missing:
        print("错误: 缺少依赖 'pdf2image'")
        print("请安装: pip install pdf2image")
        print("还需要系统依赖: sudo apt-get install poppler-utils (Linux)")
        sys.exit(1)

    if args.engine == 'paddle' and 'paddleocr' in missing:
        print("错误: 缺少依赖 'paddleocr'")
        print("请安装: pip install paddlepaddle paddleocr")
        print("或使用 --engine tesseract 选项")
        sys.exit(1)

    # 导入所需的库（此时应该都可用）
    from pdf2image import convert_from_path

    # 初始化OCR引擎
    if args.engine == 'paddle':
        from paddleocr import PaddleOCR
        print("初始化PaddleOCR引擎...")
        ocr = PaddleOCR(use_textline_orientation=True, lang='ch')
        print("PaddleOCR初始化完成")
    else:
        # Tesseract
        import pytesseract
        from PIL import Image
        print("使用Tesseract引擎")
        # 检查tesseract是否安装
        try:
            pytesseract.get_tesseract_version()
        except EnvironmentError:
            print("错误: Tesseract未安装")
            print("请安装: sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim (Linux)")
            print("或: brew install tesseract tesseract-lang (macOS)")
            sys.exit(1)

    # 转换PDF为图像
    print(f"正在转换PDF: {input_path}")
    try:
        images = convert_from_path(str(input_path), dpi=args.dpi)
    except Exception as e:
        print(f"PDF转换失败: {e}")
        print("请确保已安装poppler-utils: sudo apt-get install poppler-utils (Linux)")
        sys.exit(1)

    print(f"共 {len(images)} 页")

    # 准备Markdown内容
    md_lines = []
    md_lines.append(f"# PDF识别结果\n")
    md_lines.append(f"源文件: {input_path.name}\n")
    md_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    md_lines.append(f"引擎: {args.engine}\n")
    md_lines.append(f"页数: {len(images)}\n")

    # 处理每一页
    for page_num, image in enumerate(images, 1):
        print(f"正在识别第 {page_num}/{len(images)} 页...")
        md_lines.append(f"\n## 第 {page_num} 页\n")

        if args.engine == 'paddle':
            # 使用PaddleOCR
            # 将PIL图像转换为numpy数组
            import numpy as np
            img_np = np.array(image)
            result = ocr.predict(img_np, use_doc_orientation_classify=True)
            page_texts = []

            if result is not None:
                for line in result:
                    if line is not None:
                        for word_info in line:
                            text = word_info[1][0]
                            page_texts.append(text)

            if page_texts:
                md_lines.append("\n".join(page_texts) + "\n")
            else:
                md_lines.append("*(未识别到文本)*\n")

            print(f"  识别到 {len(page_texts)} 个文本")

        else:
            # 使用Tesseract
            import pytesseract
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            if text.strip():
                md_lines.append(text + "\n")
            else:
                md_lines.append("*(未识别到文本)*\n")

            print(f"  识别完成")

    # 保存Markdown文件
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(md_lines)

        print(f"\n识别完成!")
        print(f"输出文件: {output_path}")

    except Exception as e:
        print(f"保存文件失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()