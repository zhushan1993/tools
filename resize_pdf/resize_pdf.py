#!/usr/bin/env python3
"""
PDF页面统一大小工具
分析PDF页面大小，找出最常见的页面大小，然后将所有页面统一为该大小
"""

import sys
import os
import argparse
from collections import defaultdict

# 使用page_demo的venv中的pypdf
try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import RectangleObject
except ImportError:
    print("错误: 请先安装pypdf库")
    print("运行: pip install pypdf")
    sys.exit(1)


def analyze_pdf_pages(pdf_path):
    """分析PDF文件的所有页面大小"""
    print(f"正在分析文件: {pdf_path}")

    reader = PdfReader(pdf_path)
    page_sizes = defaultdict(int)
    page_details = []

    for i, page in enumerate(reader.pages):
        # 获取页面的媒体框（实际页面大小）
        media_box = page.mediabox
        width = float(media_box.width)
        height = float(media_box.height)

        # 取整到整数（避免浮点精度问题）
        width = round(width, 1)
        height = round(height, 1)

        size_key = (width, height)
        page_sizes[size_key] += 1
        page_details.append({
            'page_num': i + 1,
            'width': width,
            'height': height,
            'size_key': size_key
        })

    return page_sizes, page_details


def get_most_common_size(page_sizes):
    """获取最常见的页面大小"""
    if not page_sizes:
        return None

    # 按数量排序
    sorted_sizes = sorted(page_sizes.items(), key=lambda x: x[1], reverse=True)
    most_common = sorted_sizes[0]

    return most_common


def resize_pdf_to_size(input_path, output_path, target_width, target_height):
    """将PDF所有页面调整为指定大小"""
    reader = PdfReader(input_path)
    writer = PdfWriter()

    target_rect = RectangleObject((0, 0, target_width, target_height))

    for page in reader.pages:
        # 创建新页面
        new_page = writer.add_blank_page(width=target_width, height=target_height)

        # 计算缩放比例，保持宽高比
        orig_width = float(page.mediabox.width)
        orig_height = float(page.mediabox.height)

        scale_x = target_width / orig_width
        scale_y = target_height / orig_height
        scale = min(scale_x, scale_y)  # 保持比例，不拉伸

        # 计算居中位置
        scaled_width = orig_width * scale
        scaled_height = orig_height * scale
        offset_x = (target_width - scaled_width) / 2
        offset_y = (target_height - scaled_height) / 2

        # 缩放并合并页面
        page.scale_by(scale)
        new_page.merge_translated_page(page, offset_x, offset_y)

    # 保存输出文件
    with open(output_path, 'wb') as f:
        writer.write(f)

    print(f"已保存调整后的PDF: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='PDF页面统一大小工具')
    parser.add_argument('-i', '--input', default="/home/zhus/ai-space/P02_CP_DailyReport/test/朱珊-七级.pdf",
                       help='输入PDF文件路径 (默认: 测试文件)')
    parser.add_argument('-o', '--output', default="/home/zhus/ai-space/P02_CP_DailyReport/test/朱珊-七级_统一大小.pdf",
                       help='输出PDF文件路径 (默认: 测试文件输出路径)')
    args = parser.parse_args()

    input_pdf = args.input
    output_pdf = args.output

    if not os.path.exists(input_pdf):
        print(f"错误: 文件不存在: {input_pdf}")
        sys.exit(1)

    # 分析页面大小
    page_sizes, page_details = analyze_pdf_pages(input_pdf)

    # 显示分析结果
    print("\n=== 页面大小统计 ===")
    sorted_sizes = sorted(page_sizes.items(), key=lambda x: x[1], reverse=True)
    for size, count in sorted_sizes:
        print(f"  {size[0]} x {size[1]} 点: {count} 页")

    # 获取最常见的页面大小
    most_common = get_most_common_size(page_sizes)
    if most_common:
        target_size, target_count = most_common
        print(f"\n最常见的页面大小: {target_size[0]} x {target_size[1]} 点 (共{target_count}页)")

        # 调整PDF
        print("\n正在调整PDF页面大小...")
        resize_pdf_to_size(input_pdf, output_pdf, target_size[0], target_size[1])

        # 验证结果
        print("\n正在验证结果...")
        new_sizes, _ = analyze_pdf_pages(output_pdf)
        print("\n=== 输出文件页面大小统计 ===")
        for size, count in sorted(new_sizes.items(), key=lambda x: x[1], reverse=True):
            print(f"  {size[0]} x {size[1]} 点: {count} 页")

        print("\n完成!")
    else:
        print("无法确定页面大小")


if __name__ == "__main__":
    main()
