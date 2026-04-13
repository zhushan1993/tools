# PDF OCR 工具使用说明

## 概述

这是一个用于扫描版 PDF 文件 OCR 识别的 Python 工具，可以将 PDF 转换为 Markdown 文档。

## 功能特性

- ✅ 支持多页 PDF 文件
- ✅ 支持中文（简体/繁体）和英文 OCR
- ✅ 批量处理多个 PDF
- ✅ 可自定义 DPI（图像分辨率）
- ✅ 输出为 Markdown 格式
- ✅ 命令行界面，易于集成

## 安装依赖

### 系统依赖

```bash
# Ubuntu/Debian
apt-get update
apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    poppler-utils

# 验证安装
tesseract --version
pdftoppm --version
```

### Python 依赖

```bash
# 可选：如果需要 Python API 调用
pip install pdf2image pytesseract
```

## 使用方法

### 基本用法

```bash
# 单个 PDF 文件
python pdf_ocr_tool.py -i input.pdf -o output.md

# 批量处理
python pdf_ocr_tool.py -i *.pdf -o output_ --batch

# 自定义 DPI（更高分辨率 = 更好识别效果）
python pdf_ocr_tool.py -i document.pdf -o document.md --dpi 400

# 指定语言
python pdf_ocr_tool.py -i document.pdf -o document.md --lang eng
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-i, --input` | 输入 PDF 文件（必填，支持通配符） | - |
| `-o, --output` | 输出文件名或前缀 | `output_` |
| `--batch` | 批量处理模式 | False |
| `--dpi` | 图片分辨率 DPI | 300 |
| `--lang` | OCR 语言 | `chi_sim+eng` |
| `--work-dir` | 工作目录 | 当前目录 |
| `--keep-temp` | 保留临时图片文件 | False |

### 语言选项

- `chi_sim` - 简体中文
- `chi_tra` - 繁体中文
- `eng` - 英文
- `chi_sim+eng` - 简体中文 + 英文（推荐）
- `chi_tra+eng` - 繁体中文 + 英文

## 使用示例

### 示例 1：单个文件识别

```bash
cd /app/workspace
python tools/pdf_ocr/pdf_ocr_tool.py -i "扫描文档.pdf" -o "扫描文档.md"
```

### 示例 2：批量处理工作目录下的所有 PDF

```bash
cd /app/workspace
python tools/pdf_ocr/pdf_ocr_tool.py -i *.pdf -o ocr_ --batch --dpi 300
```

### 示例 3：高分辨率识别（适用于模糊文档）

```bash
python tools/pdf_ocr/pdf_ocr_tool.py -i "模糊文档.pdf" -o "模糊文档.md" --dpi 400
```

### 示例 4：保留临时图片（用于调试）

```bash
python tools/pdf_ocr/pdf_ocr_tool.py -i "文档.pdf" -o "文档.md" --keep-temp
```

## 作为 Python 模块调用

```python
from pdf_ocr_tool import PDFOCRTool

# 初始化工具
tool = PDFOCRTool(
    work_dir='/app/workspace',
    dpi=300,
    lang='chi_sim+eng'
)

# 单个 PDF
tool.ocr_pdf('input.pdf', 'output.md')

# 批量处理
pdf_files = ['doc1.pdf', 'doc2.pdf', 'doc3.pdf']
results = tool.batch_ocr(pdf_files, 'output_')

# 清理临时文件
tool.cleanup()
```

## 性能优化建议

1. **DPI 选择**
   - 清晰文档：300 DPI（默认）
   - 模糊文档：400-600 DPI
   - 超大文档：200 DPI（牺牲质量换速度）

2. **批量处理**
   - 建议分批处理，每批不超过 10 个文件
   - 可使用 `--keep-temp` 保留中间结果

3. **内存优化**
   - 处理完成后自动清理临时文件
   - 大文件建议单独处理

## 输出格式

输出为 Markdown 格式，包含：
- 分页标记
- 原始文本内容
- 保持原有段落结构

示例：
```markdown
==================================================
第 1 页
==================================================

这里是第一页的识别内容...

==================================================
第 2 页
==================================================

这里是第二页的识别内容...
```

## 故障排除

### 问题 1：找不到 tesseract 命令

```bash
# 检查安装
which tesseract

# 安装
apt-get install -y tesseract-ocr tesseract-ocr-chi-sim
```

### 问题 2：中文识别效果差

```bash
# 确保安装了中文语言包
tesseract --list-langs

# 应该看到 chi_sim 和 chi_tra
```

### 问题 3：PDF 转换失败

```bash
# 检查 poppler-utils 是否安装
pdftoppm --version

# 安装
apt-get install -y poppler-utils
```

### 问题 4：内存不足

- 降低 DPI 值（如 200）
- 分批处理文件
- 增加系统 swap 空间

## 文件结构

```
tools/pdf_ocr/
├── pdf_ocr_tool.py      # 主程序
├── README.md            # 使用说明（本文件）
└── examples/            # 示例文件（可选）
    ├── example1.pdf
    └── example1.md
```

## 版本历史

- v1.0 (2024) - 初始版本
  - 支持单文件/批量处理
  - 支持中文 OCR
  - 命令行界面
  - Python API

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系系统管理员。
