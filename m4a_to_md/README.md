# iPhone录音转Markdown工具

## 📋 功能概述

将iPhone录音文件（.m4a格式）转换为结构化的Markdown记录，支持：
- 音频转录为文本
- 自动添加时间戳
- 支持中文语音识别
- 批量处理多个文件
- 可配置的输出格式

## 🗂️ 目录结构

```
m4a_to_md/
├── input/          # 输入目录：存放.m4a录音文件
├── output/         # 输出目录：生成的.markdown文件
├── script/         # 脚本目录：主要处理脚本
├── README.md       # 本说明文档
├── requirements.txt # Python依赖
└── .venv/          # 虚拟环境目录（由setup_venvs.sh创建）
```

## 🔧 安装和设置

### 1. 创建虚拟环境

```bash
# 进入工具目录
cd /home/zhus/ai-space/tools/m4a_to_md

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Linux/macOS)
source .venv/bin/activate

# 激活虚拟环境 (Windows)
# .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 安装系统依赖

#### Ubuntu/Debian:
```bash
# 安装音频处理依赖
sudo apt-get install ffmpeg libasound2-dev portaudio19-dev

# 安装pyaudio系统依赖
sudo apt-get install python3-pyaudio
```

#### macOS:
```bash
# 使用Homebrew安装
brew install ffmpeg portaudio
```

#### Windows:
- 下载并安装 [FFmpeg](https://ffmpeg.org/download.html)
- 添加到系统PATH

## 🚀 使用方法

### 基本使用

```bash
# 确保已激活虚拟环境
source .venv/bin/activate

# 运行转换脚本
python script/m4a_to_md.py
```

默认情况下，脚本会：
1. 扫描 `input/` 目录下的所有 `.m4a` 文件
2. 将每个文件转换为对应的 `.md` 文件
3. 保存到 `output/` 目录

### 命令行选项

```bash
# 指定输入文件
python script/m4a_to_md.py -i input/录音文件.m4a

# 指定输出文件
python script/m4a_to_md.py -i input/录音文件.m4a -o output/记录.md

# 批量处理整个目录
python script/m4a_to_md.py --batch input/

# 设置语言（默认：zh-CN）
python script/m4a_to_md.py --language zh-CN

# 显示详细输出
python script/m4a_to_md.py --verbose
```

### 示例

```bash
# 转换单个文件
python script/m4a_to_md.py -i input/20260401-会议记录.m4a -o output/会议记录.md

# 批量处理
python script/m4a_to_md.py --batch input/ --output-dir output/
```

## 📝 输出格式

生成的Markdown文件包含以下结构：

```markdown
# 录音记录：文件名

**录音信息：**
- 文件名：20260401-会议记录.m4a
- 转换时间：2024-01-15 14:30:25
- 文件大小：15.2 MB
- 持续时间：00:25:18

## 转录内容

[00:00:00] 大家好，今天我们会议的主题是...
[00:01:15] 第一个议题是关于项目进度...
[00:05:30] 第二个议题是下周的工作安排...

## 关键点总结

1. 项目进度正常，需要加快前端开发
2. 下周需要完成测试环境部署
3. 需要协调设计资源

---

*转录完成时间：2024-01-15 14:35:42*
*识别引擎：speech_recognition (Google Web Speech API)*
```

## 🔌 技术实现

### 使用的库

1. **pydub** - 音频文件处理和格式转换
2. **speech_recognition** - 语音识别核心库
3. **pyaudio** - 音频输入输出支持（备用）
4. **ffmpeg** - 音频格式转换（通过pydub）

### 识别引擎支持

本工具支持多种识别引擎：

1. **Google Web Speech API**（默认）- 免费，需要网络
2. **Google Cloud Speech API** - 更准确，需要API密钥
3. **离线引擎**（如Vosk）- 本地识别，无需网络

### 音频处理流程

1. **预处理**：m4a → wav 格式转换
2. **分片处理**：长音频分割为短片段（避免超时）
3. **语音识别**：使用选定的引擎进行识别
4. **后处理**：文本清理、时间戳添加
5. **格式生成**：转换为Markdown格式

## ⚙️ 配置选项

可以通过修改 `script/config.py` 或使用命令行参数配置：

```python
# 默认配置
DEFAULT_CONFIG = {
    'language': 'zh-CN',      # 识别语言
    'chunk_duration': 30,     # 分片时长（秒）
    'engine': 'google',       # 识别引擎
    'api_key': None,          # API密钥（如果需要）
    'output_format': 'markdown',  # 输出格式
    'add_timestamps': True,   # 是否添加时间戳
    'generate_summary': True, # 是否生成摘要
}
```

## 🐛 常见问题

### Q1: 无法读取m4a文件
**解决方法**：
- 确保已安装FFmpeg：`ffmpeg -version`
- 检查文件格式是否正确
- 尝试使用其他音频文件测试

### Q2: 识别结果为空或错误
**解决方法**：
- 检查网络连接（如果使用在线API）
- 调整音频质量，确保清晰度
- 尝试使用不同的语言设置
- 考虑使用离线引擎

### Q3: 内存不足或处理缓慢
**解决方法**：
- 减少 `chunk_duration` 值
- 使用更轻量的识别引擎
- 分批处理大型文件

### Q4: 无法安装pyaudio
**解决方法**：
- 先安装系统依赖（见上文）
- 尝试使用预编译版本：`pip install pipwin && pipwin install pyaudio`（Windows）
- 或使用替代方案：`conda install pyaudio`

## 🔄 更新和维护

### 更新依赖
```bash
source .venv/bin/activate
pip install --upgrade -r requirements.txt
```

### 导出当前依赖
```bash
source .venv/bin/activate
pip freeze > requirements.txt
```

### 测试功能
```bash
# 运行测试脚本
python script/test_conversion.py
```

## 📁 文件说明

- `script/m4a_to_md.py` - 主转换脚本
- `script/audio_utils.py` - 音频处理工具函数
- `script/text_utils.py` - 文本处理工具函数
- `script/config.py` - 配置文件
- `script/test_conversion.py` - 测试脚本
- `input/` - 输入文件目录
- `output/` - 输出文件目录

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送到分支：`git push origin feature/new-feature`
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。

## 📞 联系方式

如有问题或建议，请联系工具维护者。

---

**最后更新**：2026-04-09
**Python版本**：3.12
**主要依赖**：speech_recognition, pydub