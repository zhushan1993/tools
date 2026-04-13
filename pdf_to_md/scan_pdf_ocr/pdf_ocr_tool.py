#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF OCR 批量识别工具
=====================
功能：将扫描版 PDF 文件转换为 Markdown 文档
支持：多页 PDF、中文 OCR、批量处理

依赖安装：
    apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-chi-tra poppler-utils
    pip install pdf2image pytesseract

使用方法：
    python pdf_ocr_tool.py --help
    python pdf_ocr_tool.py -i input.pdf -o output.md
    python pdf_ocr_tool.py -i *.pdf -o output_  --batch

作者：Copaw Assistant
日期：2024
"""

import os
import sys
import argparse
import subprocess
import shutil
from pathlib import Path
from datetime import datetime


class PDFOCRTool:
    """PDF OCR 识别工具类"""
    
    def __init__(self, work_dir=None, dpi=300, lang='chi_sim+eng'):
        """
        初始化 OCR 工具
        
        Args:
            work_dir: 工作目录，默认当前目录
            dpi: 图片分辨率，默认 300
            lang: OCR 语言，默认简体中文 + 英文
        """
        self.work_dir = Path(work_dir or '.')
        self.dpi = dpi
        self.lang = lang
        self.temp_image_dir = self.work_dir / 'temp_pdf_images'
        
    def pdf_to_images(self, pdf_path, output_prefix='page'):
        """
        将 PDF 转换为图片
        
        Args:
            pdf_path: PDF 文件路径
            output_prefix: 输出图片前缀
            
        Returns:
            list: 生成的图片文件列表
        """
        pdf_path = Path(pdf_path)
        self.temp_image_dir.mkdir(exist_ok=True)
        
        output_path = self.temp_image_dir / f'{output_prefix}-%d'
        
        cmd = [
            'pdftoppm',
            '-png',
            f'-r{self.dpi}',
            str(pdf_path),
            str(output_path)
        ]
        
        print(f"  转换 PDF 为图片：{pdf_path.name} (DPI={self.dpi})")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  ❌ PDF 转换失败：{result.stderr}")
            return []
        
        # 获取生成的图片列表
        images = sorted(self.temp_image_dir.glob(f'{output_prefix}-*.png'))
        print(f"  ✓ 生成 {len(images)} 张图片")
        
        return images
    
    def ocr_image(self, image_path):
        """
        对单张图片进行 OCR 识别
        
        Args:
            image_path: 图片路径
            
        Returns:
            str: 识别出的文字内容
        """
        output_base = image_path.parent / image_path.stem
        
        cmd = [
            'tesseract',
            str(image_path),
            str(output_base),
            '-l', self.lang,
            '--psm', '6'  # 假设是均匀文本块
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  ❌ OCR 失败：{image_path.name}")
            return ""
        
        # 读取识别结果
        txt_file = output_base.with_suffix('.txt')
        if txt_file.exists():
            with open(txt_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def ocr_pdf(self, pdf_path, output_md=None):
        """
        对 PDF 进行完整 OCR 识别并生成 Markdown
        
        Args:
            pdf_path: PDF 文件路径
            output_md: 输出 Markdown 文件路径（可选）
            
        Returns:
            str: 识别的完整文本内容
        """
        pdf_path = Path(pdf_path)
        print(f"\n{'='*60}")
        print(f"开始处理：{pdf_path.name}")
        print(f"{'='*60}")
        
        # 1. 转换为图片
        images = self.pdf_to_images(pdf_path)
        if not images:
            return ""
        
        # 2. 对每张图片进行 OCR
        all_text = []
        for i, image in enumerate(images, 1):
            print(f"  识别第 {i}/{len(images)} 页：{image.name}")
            text = self.ocr_image(image)
            if text:
                all_text.append(f"\n{'='*50}\n第 {i} 页\n{'='*50}\n\n{text}\n")
        
        # 3. 合并结果
        full_text = "\n".join(all_text)
        
        # 4. 保存为文件
        if output_md is None:
            output_md = pdf_path.with_suffix('.md')
        else:
            output_md = Path(output_md)
        
        with open(output_md, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print(f"\n✓ 完成！输出文件：{output_md}")
        print(f"  总页数：{len(images)}")
        print(f"  文件大小：{output_md.stat().st_size / 1024:.1f} KB")
        
        return full_text
    
    def batch_ocr(self, pdf_files, output_prefix='output_'):
        """
        批量处理多个 PDF 文件
        
        Args:
            pdf_files: PDF 文件列表
            output_prefix: 输出文件前缀
            
        Returns:
            dict: 处理结果 {文件名：输出文件路径}
        """
        results = {}
        
        for i, pdf_file in enumerate(pdf_files, 1):
            pdf_file = Path(pdf_file)
            print(f"\n[{i}/{len(pdf_files)}] 处理：{pdf_file.name}")
            
            # 生成输出文件名
            output_md = self.work_dir / f"{output_prefix}{pdf_file.stem}.md"
            
            # 处理 PDF
            self.ocr_pdf(pdf_file, output_md)
            results[pdf_file.name] = output_md
        
        return results
    
    def cleanup(self):
        """清理临时文件"""
        if self.temp_image_dir.exists():
            shutil.rmtree(self.temp_image_dir)
            print(f"\n清理临时目录：{self.temp_image_dir}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='PDF OCR 批量识别工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单个 PDF
  python pdf_ocr_tool.py -i document.pdf -o document.md
  
  # 批量处理
  python pdf_ocr_tool.py -i *.pdf -o output_ --batch
  
  # 自定义 DPI
  python pdf_ocr_tool.py -i document.pdf -o document.md --dpi 400
  
  # 指定语言
  python pdf_ocr_tool.py -i document.pdf -o document.md --lang eng
        """
    )
    
    parser.add_argument('-i', '--input', nargs='+', required=True,
                       help='输入 PDF 文件（支持通配符）')
    parser.add_argument('-o', '--output', default='output_',
                       help='输出文件名或前缀（批量模式下为前缀）')
    parser.add_argument('--batch', action='store_true',
                       help='批量处理模式')
    parser.add_argument('--dpi', type=int, default=300,
                       help='图片分辨率 DPI（默认 300）')
    parser.add_argument('--lang', default='chi_sim+eng',
                       help='OCR 语言（默认 chi_sim+eng）')
    parser.add_argument('--work-dir', default=None,
                       help='工作目录（默认当前目录）')
    parser.add_argument('--keep-temp', action='store_true',
                       help='保留临时图片文件')
    
    args = parser.parse_args()
    
    # 展开通配符
    input_files = []
    for pattern in args.input:
        input_files.extend(Path.cwd().glob(pattern))
    
    if not input_files:
        print("❌ 未找到任何 PDF 文件")
        sys.exit(1)
    
    # 初始化工具
    tool = PDFOCRTool(
        work_dir=args.work_dir,
        dpi=args.dpi,
        lang=args.lang
    )
    
    print(f"\n{'='*60}")
    print(f"PDF OCR 批量识别工具")
    print(f"{'='*60}")
    print(f"工作目录：{tool.work_dir}")
    print(f"DPI: {tool.dpi}")
    print(f"语言：{tool.lang}")
    print(f"待处理文件：{len(input_files)}")
    
    # 处理文件
    if args.batch or len(input_files) > 1:
        results = tool.batch_ocr(input_files, args.output)
    else:
        output_file = args.output if Path(args.output).suffix == '.md' else None
        tool.ocr_pdf(input_files[0], output_file)
        results = {input_files[0].name: output_file or input_files[0].with_suffix('.md')}
    
    # 清理临时文件
    if not args.keep_temp:
        tool.cleanup()
    
    print(f"\n{'='*60}")
    print(f"处理完成！")
    print(f"{'='*60}")
    for pdf_name, md_path in results.items():
        print(f"  ✓ {pdf_name} → {md_path}")


if __name__ == '__main__':
    main()
