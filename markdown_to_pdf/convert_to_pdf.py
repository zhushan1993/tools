#!/usr/bin/env python3
"""
将README_交付说明.md转换为PDF的脚本
使用markdown库 + weasyprint，确保格式正确
"""

import os
import sys
from pathlib import Path

# 注意：请先激活虚拟环境再运行此脚本
# source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate     # Windows

def read_markdown(file_path):
    """读取Markdown文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def preprocess_markdown(md_content):
    """预处理Markdown，确保列表和表格前有空行"""
    import re

    lines = md_content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        line_stripped = line.strip()

        # 检查是否需要在前面插入空行
        need_empty_line = False

        # 情况1: 当前行是列表项（以- 或数字. 开头）
        is_list_item = (line_stripped.startswith('- ') or
                       re.match(r'^\d+\.\s', line_stripped))

        # 情况2: 当前行是表格（以|开头）
        is_table_row = line_stripped.startswith('|')

        if is_list_item or is_table_row:
            # 检查前一行是否非空且不是同类内容
            if i > 0:
                prev_line = lines[i-1].strip()
                if (prev_line and
                    not prev_line.startswith('- ') and
                    not re.match(r'^\d+\.\s', prev_line) and
                    not prev_line.startswith('|') and
                    not prev_line.startswith('```')):
                    need_empty_line = True

        if need_empty_line:
            result.append('')

        result.append(line)
        i += 1

    return '\n'.join(result)

def markdown_to_html(md_content):
    """使用markdown库正确转换"""
    import markdown

    # 预处理Markdown
    md_content = preprocess_markdown(md_content)

    # 使用多个扩展来确保正确解析（不使用nl2br，避免破坏列表）
    html = markdown.markdown(
        md_content,
        extensions=[
            'tables',           # 表格支持
            'fenced_code',      # 代码块支持
            'attr_list',        # 属性列表
            'def_list',         # 定义列表
            'md_in_html',       # HTML中的Markdown
            'sane_lists',       # 更好的列表处理
        ]
    )
    return html

def create_full_html(body_content):
    """创建完整的HTML文档，改进样式"""
    # 使用Windows字体（WSL挂载）
    font_path = "/mnt/c/Windows/Fonts/msyh.ttc"
    font_bold_path = "/mnt/c/Windows/Fonts/msyhbd.ttc"

    font_css = ""
    if os.path.exists(font_path):
        font_css = f"""
        @font-face {{
            font-family: 'MicrosoftYaHei';
            src: url('file://{font_path}') format('truetype');
            font-weight: normal;
            font-style: normal;
        }}
        """
    if os.path.exists(font_bold_path):
        font_css += f"""
        @font-face {{
            font-family: 'MicrosoftYaHei';
            src: url('file://{font_bold_path}') format('truetype');
            font-weight: bold;
            font-style: normal;
        }}
        """

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>进京检查站运行监测页面 - 交付说明</title>
    <style>
        {font_css}

        * {{
            box-sizing: border-box;
        }}

        @page {{
            size: A4;
            margin: 2.5cm;
        }}

        body {{
            font-family: 'MicrosoftYaHei', 'Microsoft YaHei', 'SimHei', 'PingFang SC', 'Heiti TC', sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            font-size: 11pt;
            max-width: 100%;
            margin: 0;
            padding: 0;
        }}

        h1 {{
            font-size: 18pt;
            color: #1a73e8;
            border-bottom: 2px solid #1a73e8;
            padding-bottom: 10px;
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: bold;
        }}

        h2 {{
            font-size: 14pt;
            color: #202124;
            margin-top: 22px;
            margin-bottom: 12px;
            font-weight: bold;
            padding-bottom: 4px;
            border-bottom: 1px solid #e8eaed;
        }}

        h3 {{
            font-size: 12pt;
            color: #202124;
            margin-top: 18px;
            margin-bottom: 10px;
            font-weight: bold;
        }}

        h4 {{
            font-size: 11pt;
            color: #5f6368;
            margin-top: 14px;
            margin-bottom: 8px;
            font-weight: bold;
        }}

        p {{
            margin: 4px 0;
            text-align: justify;
        }}

        ul, ol {{
            margin: 8px 0;
            padding-left: 28px;
        }}

        li {{
            margin: 4px 0;
        }}

        /* 嵌套列表 - 确保多级缩进清晰 */
        ul ul, ol ol, ul ol, ol ul {{
            margin: 4px 0;
            padding-left: 24px;
        }}

        ul ul ul, ol ol ol, ul ol ul, ol ul ol,
        ul ul ol, ol ol ul, ul ol ol, ol ul ul {{
            padding-left: 28px;
        }}

        code {{
            background-color: #f1f3f4;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 10pt;
            color: #d93025;
        }}

        pre {{
            background-color: #f8f9fa;
            padding: 12px 16px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 12px 0;
            border: 1px solid #e8eaed;
        }}

        pre code {{
            background: none;
            padding: 0;
            color: #202124;
            font-size: 9.5pt;
            line-height: 1.5;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 12px 0;
            font-size: 10pt;
        }}

        th, td {{
            border: 1px solid #dadce0;
            padding: 8px 12px;
            text-align: left;
        }}

        th {{
            background-color: #f1f3f4;
            font-weight: bold;
            color: #202124;
        }}

        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}

        tr:hover {{
            background-color: #e8f0fe;
        }}

        hr {{
            border: none;
            border-top: 1px solid #e8eaed;
            margin: 20px 0;
        }}

        blockquote {{
            border-left: 4px solid #1a73e8;
            padding-left: 16px;
            margin: 12px 0;
            color: #5f6368;
            background-color: #e8f0fe;
            padding: 10px 16px;
            border-radius: 0 4px 4px 0;
        }}

        strong {{
            color: #202124;
            font-weight: bold;
        }}

        em {{
            font-style: italic;
            color: #5f6368;
        }}

        a {{
            color: #1a73e8;
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        /* 目录树样式 */
        pre:has(code) {{
            line-height: 1.4;
        }}
    </style>
</head>
<body>
{body_content}
</body>
</html>"""

def main():
    # 解析命令行参数
    if len(sys.argv) < 2:
        print("用法: python convert_to_pdf.py <markdown文件路径>")
        print("示例: python convert_to_pdf.py /path/to/README.md")
        return 1

    md_file = Path(sys.argv[1])
    if not md_file.exists():
        print(f"错误：找不到文件 {md_file}")
        return 1

    base_dir = md_file.parent
    html_file = base_dir / (md_file.stem + '.html')
    pdf_file = base_dir / (md_file.stem + '.pdf')

    print(f"读取: {md_file}")
    md_content = read_markdown(md_file)

    print("转换为HTML (使用markdown库)...")
    body_html = markdown_to_html(md_content)
    full_html = create_full_html(body_html)

    print(f"写入HTML: {html_file}")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)

    # 使用weasyprint转换PDF
    try:
        from weasyprint import HTML
        print("使用WeasyPrint转换PDF...")
        HTML(string=full_html).write_pdf(pdf_file)
        print(f"✅ 成功生成PDF: {pdf_file}")
        return 0
    except ImportError:
        print("⚠️  未安装weasyprint")
    except Exception as e:
        print(f"⚠️  PDF转换出错: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)
    print(f"已生成HTML文件: {html_file}")
    print("\n备选方案 - 使用浏览器生成PDF:")
    print("   1. 在浏览器中打开 HTML 文件")
    print("   2. 按 Ctrl + P 打开打印对话框")
    print("   3. 选择'保存为PDF'")
    print("="*70)

    return 0

if __name__ == '__main__':
    sys.exit(main())
