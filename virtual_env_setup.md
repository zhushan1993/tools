# 工具目录虚拟环境管理说明

## 📋 概述

本目录包含多个独立的Python工具，每个工具都有独立的虚拟环境，确保依赖隔离和版本兼容性。

## 🗂️ 工具目录结构

```
tools/
├── markdown_to_pdf/          # Markdown转PDF工具 (.venv)
├── resize_pdf/               # PDF页面调整工具 (.venv)
├── pdf_to_md/
│   ├── handwrite_pdf/        # 手写体PDF转Markdown (.venv)
│   ├── scan_pdf_ocr/         # 扫描版PDF OCR工具 (.venv)
│   └── venv_old/             # 旧的统一虚拟环境 (可删除)
├── merge_csv/                # CSV合并工具 (仅标准库，无需venv)
├── m4a_to_md/                # iPhone录音转Markdown工具 (.venv)
└── setup_venvs.sh            # 虚拟环境设置脚本
```

## 🔧 虚拟环境配置

### 已创建的虚拟环境

| 工具目录 | 虚拟环境位置 | 主要依赖 |
|---------|-------------|---------|
| `markdown_to_pdf/` | `.venv/` | `markdown>=3.5`, `weasyprint>=59.0` |
| `resize_pdf/` | `.venv/` | `pypdf>=4.0.0` |
| `pdf_to_md/handwrite_pdf/` | `.venv/` | `pdf2image>=1.16.0`, `paddleocr>=2.6.0`, `paddlepaddle>=2.4.0`, `pytesseract>=0.3.10` |
| `pdf_to_md/scan_pdf_ocr/` | `.venv/` | `pdf2image>=1.16.0`, `pytesseract>=0.3.10`, `Pillow>=9.0.0` |
| `m4a_to_md/` | `.venv/` | `pydub>=0.25.1`, `SpeechRecognition>=3.10.0`, `chardet>=5.2.0`, `tqdm>=4.66.0`, `jieba>=0.42.1` |

### 无需虚拟环境的工具

- **`merge_csv/`**：仅使用Python标准库 (`os`, `sys`, `glob`)

## 🚀 使用方法

### 1. 激活虚拟环境

```bash
# 进入工具目录
cd /home/zhus/ai-space/tools/markdown_to_pdf

# 激活虚拟环境 (Linux/macOS)
source .venv/bin/activate

# 激活虚拟环境 (Windows)
# .venv\Scripts\activate

# 验证激活
python --version  # 应显示Python 3.12
pip list          # 查看已安装的包
```

### 2. 运行工具

```bash
# markdown_to_pdf
source .venv/bin/activate
python convert_to_pdf.py input.md output.pdf

# resize_pdf
source .venv/bin/activate
python resize_pdf.py -i input.pdf -o output.pdf

# handwrite_pdf
source .venv/bin/activate
python handwrite_pdf_to_md.py input.pdf output.md --engine paddle

# scan_pdf_ocr
source .venv/bin/activate
python pdf_ocr_tool.py -i input.pdf -o output.md

# m4a_to_md
source .venv/bin/activate
python script/m4a_to_md.py -i input/录音文件.m4a -o output/记录.md
```

### 3. 退出虚拟环境

```bash
deactivate
```

## ⚙️ 系统依赖

某些工具需要系统级依赖包：

### 1. `markdown_to_pdf/` 系统依赖
```bash
# Ubuntu/Debian
sudo apt-get install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
  libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# macOS
brew install cairo pango gdk-pixbuf libffi
```

### 2. `pdf_to_md/` 工具系统依赖
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim \
  tesseract-ocr-chi-tra poppler-utils

# macOS
brew install tesseract tesseract-lang poppler

# Windows
# 下载安装 Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
# 下载安装 Poppler: https://github.com/oschwartz10612/poppler-windows/releases
```

### 3. `m4a_to_md/` 工具系统依赖
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg libasound2-dev portaudio19-dev python3-pyaudio

# macOS
brew install ffmpeg portaudio

# Windows
# 1. 下载安装 FFmpeg: https://ffmpeg.org/download.html
# 2. 添加到系统PATH
# 3. 对于pyaudio: pip install pipwin && pipwin install pyaudio
```

## 🔄 重新创建虚拟环境

如果需要重新创建所有虚拟环境：

```bash
# 进入tools目录
cd /home/zhus/ai-space/tools

# 运行设置脚本
chmod +x setup_venvs.sh
./setup_venvs.sh
```

## 🧹 清理旧环境

建议删除旧的统一虚拟环境，避免混淆：

```bash
rm -rf pdf_to_md/venv_old pdf_to_md/venv
```

## 📝 各工具详细说明

### 1. `markdown_to_pdf/`
- **功能**：将Markdown文件转换为PDF
- **主要脚本**：`convert_to_pdf.py`
- **依赖**：`markdown`, `weasyprint`
- **注意事项**：`weasyprint` 需要系统图形库支持

### 2. `resize_pdf/`
- **功能**：统一PDF页面大小
- **主要脚本**：`resize_pdf.py`
- **依赖**：`pypdf`
- **使用示例**：`python resize_pdf.py -i input.pdf -o output.pdf`

### 3. `pdf_to_md/handwrite_pdf/`
- **功能**：手写体PDF文字识别
- **主要脚本**：`handwrite_pdf_to_md.py`
- **依赖**：`paddleocr`, `paddlepaddle`, `pdf2image`
- **引擎选择**：`--engine paddle` (推荐) 或 `--engine tesseract`

### 4. `pdf_to_md/scan_pdf_ocr/`
- **功能**：扫描版PDF文字识别
- **主要脚本**：`pdf_ocr_tool.py`, `ocr.sh`
- **依赖**：`pdf2image`, `pytesseract`, `Pillow`
- **注意**：需要系统安装 `tesseract-ocr` 和 `poppler-utils`

### 5. `merge_csv/`
- **功能**：合并多个CSV文件
- **主要脚本**：`merge_csv.py`
- **依赖**：无（仅标准库）
- **使用**：直接运行 `python merge_csv.py`

### 6. `m4a_to_md/`
- **功能**：iPhone录音文件转Markdown记录
- **主要脚本**：`script/m4a_to_md.py`
- **依赖**：`pydub`, `SpeechRecognition`, `chardet`, `tqdm`, `jieba`
- **系统依赖**：`FFmpeg`, `portaudio`（部分系统需要）
- **使用示例**：`python script/m4a_to_md.py -i input/录音.m4a -o output/记录.md`
- **注意**：默认使用Google Web Speech API，需要网络连接。如需离线识别，可安装`vosk`或`whisper`

## ❓ 常见问题

### Q1: 激活虚拟环境后提示"command not found"
- 确保虚拟环境已创建：检查目录中是否有 `.venv/` 文件夹
- 确保使用正确的激活命令：Linux/macOS用 `source .venv/bin/activate`，Windows用 `.venv\Scripts\activate`

### Q2: 工具运行时缺少依赖
- 确保已激活正确的虚拟环境
- 检查 `requirements.txt` 是否完整
- 对于系统依赖，请参考上面的系统依赖部分

### Q3: `weasyprint` 安装失败
- 安装系统依赖：`sudo apt-get install libcairo2 libpango-1.0-0 ...`
- 或使用其他PDF生成库（如 `xhtml2pdf`）

### Q4: `paddleocr` 安装缓慢
- `paddleocr` 和 `paddlepaddle` 包较大，安装需要时间
- 可以使用国内镜像加速：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple paddleocr`

## 📁 依赖文件说明

每个工具目录包含以下文件：

- `requirements.txt`：Python依赖列表
- `.venv/`：虚拟环境目录（由 `setup_venvs.sh` 创建）
- 主脚本文件（如 `*.py`, `*.sh`）

## 🔧 自定义配置

### 创建新的虚拟环境
```bash
cd /home/zhus/ai-space/tools/new_tool
python -m venv .venv
source .venv/bin/activate
pip install package1 package2
```

### 导出依赖
```bash
source .venv/bin/activate
pip freeze > requirements.txt
```

### 更新依赖
```bash
source .venv/bin/activate
pip install --upgrade -r requirements.txt
```

## 📞 维护信息

- **创建日期**：2026-04-09
- **Python版本**：3.12
- **虚拟环境工具**：Python venv
- **依赖管理**：requirements.txt
- **设置脚本**：`setup_venvs.sh`

---

> **提示**：使用独立的虚拟环境可以避免依赖冲突，每个工具都可以独立更新和维护。