# Markdown转Word工具

基于模板的Markdown转Word文档转换器，支持样式映射配置。

## 功能特性

- 基于Word模板转换Markdown文档
- 自动识别模板封面，保留封面内容
- 支持标题、段落、列表、表格的样式映射
- 可配置的样式映射（JSON配置文件）
- 命令行接口，易于集成到工作流

## 安装

### 1. 虚拟环境设置

此工具使用独立的虚拟环境管理。运行以下命令创建虚拟环境：

```bash
cd /home/zhus/ai-space/tools
./setup_venvs.sh
```

或者手动创建虚拟环境：

```bash
cd /home/zhus/ai-space/tools/md_to_word
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 依赖

- Python 3.6+
- python-docx >= 1.1.0

## 使用方法

### 基本用法

```bash
cd /home/zhus/ai-space/tools/md_to_word
source .venv/bin/activate
python md_to_word.py input.md output.docx
```

### 完整参数

```bash
python md_to_word.py input.md output.docx \
  --template config/templates/default.docx \
  --style-config config/style_mapping.json \
  --verbose
```

**参数说明：**
- `input.md`：输入的Markdown文件（必需）
- `output.docx`：输出的Word文档（必需）
- `--template`：模板Word文档路径（可选，默认使用 `config/templates/default.docx`）
- `--style-config`：样式映射JSON配置文件路径（可选，默认使用 `config/style_mapping.json`）
- `--verbose`：显示详细输出信息

## 配置文件

### 样式映射配置

配置文件：`config/style_mapping.json`

```json
{
  "markdown_to_style": {
    "# ": "文档标题",
    "## ": "一级标题",
    "### ": "二级标题",
    "#### ": "三级标题",
    "普通段落": "缩进正文",
    "表格单元格": "表文字",
    "无序列表": "List Paragraph",
    "有序列表": "List Paragraph"
  },
  "default_styles": {
    "paragraph": "缩进正文",
    "table_cell": "表文字",
    "fallback": "Normal"
  },
  "template_settings": {
    "cover_end_markers": ["一、", "背景", "## ", "# "],
    "preserve_cover": true
  }
}
```

### 模板文件

默认模板：`config/templates/default.docx`

模板文档应包含以下样式（或类似样式）：
- `缩进正文`：普通段落样式
- `一级标题`：一级标题样式
- `二级标题`：二级标题样式
- `三级标题`：三级标题样式
- `表文字`：表格单元格样式
- `List Paragraph`：列表段落样式
- `Normal`：后备样式

## 使用示例

### 示例1：基本转换

```bash
# 使用默认模板和配置
python md_to_word.py tests/test_sample.md tests/output_basic.docx
```

### 示例2：使用自定义模板

```bash
# 使用自定义模板
python md_to_word.py input.md output.docx \
  --template /path/to/your/template.docx
```

### 示例3：使用自定义样式映射

```bash
# 使用自定义样式配置
python md_to_word.py input.md output.docx \
  --style-config custom_styles.json
```

### 示例4：从其他项目调用

```bash
# 从P02_ManagementMeasure项目调用
cd /home/zhus/ai-space/P02_ManagementMeasure
../tools/md_to_word/.venv/bin/python ../tools/md_to_word/md_to_word.py \
  plan/进京检查站联合管理办法调研方案（详细版）.md \
  doc/调研方案_new.docx \
  --template doc/ver/进京检查站联合管理办法调研方案v0-20260408.docx
```

## 测试

### 创建测试文件

创建测试Markdown文件：`tests/test_sample.md`

```markdown
# 测试文档标题

## 一级标题

这是一个测试文档，用于验证Markdown到Word的转换。

### 二级标题

这是二级标题下的内容。

#### 三级标题

这是三级标题下的内容。

- 无序列表项1
- 无序列表项2
- 无序列表项3

1. 有序列表项1
2. 有序列表项2
3. 有序列表项3

| 表头1 | 表头2 | 表头3 |
|-------|-------|-------|
| 单元格1 | 单元格2 | 单元格3 |
| 单元格4 | 单元格5 | 单元格6 |

**加粗文本** 和普通文本混合。
```

### 运行测试

```bash
cd /home/zhus/ai-space/tools/md_to_word
source .venv/bin/activate

# 运行转换测试
python md_to_word.py tests/test_sample.md tests/output_test.docx --verbose

# 检查输出文件
ls -la tests/output_test.docx
```

## 故障排除

### 常见问题

1. **模板文件不存在**
   ```
   错误：默认模板不存在
   ```
   **解决方案**：使用 `--template` 参数指定模板文件路径。

2. **样式名称不匹配**
   ```
   KeyError: '样式名称'
   ```
   **解决方案**：检查模板中的样式名称，更新 `style_mapping.json` 文件。

3. **Markdown格式解析错误**
   **解决方案**：确保Markdown文件使用标准格式，避免嵌套复杂结构。

4. **虚拟环境问题**
   **解决方案**：重新运行 `./setup_venvs.sh` 或手动创建虚拟环境。

### 调试技巧

1. 使用 `--verbose` 参数查看详细日志
2. 检查模板文档中的样式名称
3. 简化Markdown文件测试基本功能

## 与原项目的兼容性

此工具从 `P02_ManagementMeasure/script/convert_md_to_docx_final.py` 移植而来，保持向后兼容性。

**原项目可继续使用原脚本**：
```bash
cd /home/zhus/ai-space/P02_ManagementMeasure
venv/bin/python script/convert_md_to_docx_final.py
```

**或使用新工具**：
```bash
cd /home/zhus/ai-space/P02_ManagementMeasure
../tools/md_to_word/.venv/bin/python ../tools/md_to_word/md_to_word.py \
  plan/进京检查站联合管理办法调研方案（详细版）.md \
  doc/调研方案_new.docx \
  --template doc/ver/进京检查站联合管理办法调研方案v0-20260408.docx
```

## 文件结构

```
md_to_word/
├── .venv/                    # 虚拟环境
├── README.md                # 本文件
├── requirements.txt         # Python依赖
├── md_to_word.py           # 主转换脚本
├── config/                 # 配置目录
│   ├── style_mapping.json  # 样式映射配置
│   └── templates/          # 模板目录
│       └── default.docx    # 默认模板
├── input/                  # 输入目录（可选）
├── output/                 # 输出目录（可选）
└── tests/                  # 测试目录
    ├── test_sample.md      # 测试Markdown文件
    └── test_conversion.py  # 测试脚本（可选）
```

## 后续优化建议

1. **批量转换**：支持目录批量处理
2. **样式预览**：添加样式检查和预览功能
3. **模板管理**：模板文件版本管理
4. **扩展性**：支持插件式Markdown解析器
5. **性能优化**：大文档处理优化

## 许可证

内部使用工具