# ============================================================
# Python 开发环境基础镜像
# 用法：在具体项目下创建 docker-compose.yml 引用此镜像
# 或直接：
#   docker build -t dev-py312 -f tools/docker/Dockerfile .
# ============================================================

FROM python:3.12-slim

# 避免 Python 写 .pyc，并强制 stdout/stderr 无缓冲（容器日志友好）
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 系统依赖（按需增减）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
