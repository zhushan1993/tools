# tools/backup — WSL ↔ G 盘双向同步工具

## 使用

```bash
cd tools/backup

# 预览（推荐先跑一次看效果）
./sync.sh to-g --dry-run

# WSL → G 盘
./sync.sh to-g

# G 盘 → WSL
./sync.sh from-g
```

## 选项

| 参数 | 作用 |
|---|---|
| `--dry-run` | 预览模式：只显示会传输哪些文件，不实际拷贝 |
| `--include-git` | 包含 `.git` 目录（默认排除） |
| `--progress` | 显示每个文件的实时传输进度 |
| `-h, --help` | 显示帮助 |

## 排除规则

默认排除以下内容（见 `sync.conf`）：

- 虚拟环境：`venv/`, `.venv/`, `env/`, `pdf_venv/` 等
- 编译缓存：`__pycache__/`, `*.pyc`, `*.pyo`, `*.egg-info/`
- 类型/测试缓存：`.mypy_cache/`, `.pytest_cache/`
- 版本控制：`.git/`（可用 `--include-git` 包含）
- IDE 配置：`.idea/`, `.vscode/`
- Claude Code：`.claude/`
- Windows/macOS 系统残留：`$RECYCLE.BIN/`, `.DS_Store`, `.Spotlight*/` 等
- 前端构建：`node_modules/`, `dist/`, `build/`

## 快速收工 alias（可选）

```bash
echo 'alias backup="~/ai-space/tools/backup/sync.sh to-g --progress"' >> ~/.bashrc
source ~/.bashrc

# 收工时只需：
backup
```

## 环境问题

虚拟环境（venv）默认被排除——它们文件多、体积大、不适合同步。

**解决方法**（任选）：
1. **手动重建**：到目标端项目目录下重新 `python -m venv venv && pip install -r requirements.txt`
2. **Docker**：用容器替代 venv，详见 `tools/docker/`

  ```bash
  # 以 P01_CheckPoint 为例
  cd P01_CheckPoint
  docker compose -f ../tools/docker/compose-examples/P01_CheckPoint-docker-compose.yml up
  ```
  代码挂载为 volume，同步只传源码即可。
