#!/usr/bin/env bash
# ============================================================
# sync.sh — WSL ↔ G 盘双向同步工具
#
# 用法：
#   ./sync.sh to-g                WSL → G 盘
#   ./sync.sh from-g              G 盘 → WSL
#   ./sync.sh to-g --dry-run      预览模式（不实际传输）
#   ./sync.sh to-g --include-git  同步时包含 .git 目录
#   ./sync.sh to-g --progress     显示每个文件进度
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONF_FILE="$SCRIPT_DIR/sync.conf"

# ---------- 颜色 ----------
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ---------- 加载配置 ----------
if [ ! -f "$CONF_FILE" ]; then
    echo -e "${RED}[错误] 配置文件不存在: $CONF_FILE${NC}"
    exit 1
fi
source "$CONF_FILE"

# ---------- 解析参数 ----------
DIRECTION=""
DRY_RUN=""
INCLUDE_GIT=false
SHOW_PROGRESS=false

usage() {
    echo "用法: $0 {to-g|from-g} [选项]"
    echo ""
    echo "方向:"
    echo "  to-g       WSL (/home/zhus/ai-space) → G 盘 (/mnt/g/ai-space)"
    echo "  from-g     G 盘 → WSL"
    echo ""
    echo "选项:"
    echo "  --dry-run       预览模式，不实际传输"
    echo "  --include-git   包含 .git 目录（默认排除）"
    echo "  --progress      显示每个文件的传输进度"
    echo "  -h, --help      显示此帮助"
    exit 0
}

while [ $# -gt 0 ]; do
    case "$1" in
        to-g|to_g)
            DIRECTION="to-g"
            SRC="$SRC_HOME"
            DST="$DST_G_DRIVE"
            shift
            ;;
        from-g|from_g)
            DIRECTION="from-g"
            SRC="$DST_G_DRIVE"
            DST="$SRC_HOME"
            shift
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --include-git)
            INCLUDE_GIT=true
            shift
            ;;
        --progress)
            SHOW_PROGRESS=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}[错误] 未知参数: $1${NC}"
            usage
            ;;
    esac
done

if [ -z "$DIRECTION" ]; then
    echo -e "${RED}[错误] 请指定方向: to-g 或 from-g${NC}"
    usage
fi

# ---------- 路径检查 ----------
if [ ! -d "$SRC" ]; then
    echo -e "${RED}[错误] 源目录不存在: $SRC${NC}"
    exit 1
fi

# ---------- 构建 rsync 参数 ----------
# 注意：目标盘是 NTFS 时，Linux 特有属性无法写入。不使用 -a（archive），
# 而是手动组合 -rltvh，跳过 owner/group/perms/devices/specials，
# 否则每次同步都会因"属性不一致"而反复重传。
RSYNC_OPTS=(
    -rlvh                                  # recursive, links, verbose, human
    --size-only                            # 只看大小判断是否传输，跳过时间戳（NTFS 时间戳写不上）
    --delete                               # 删除目标端已不存在的文件
    --ignore-errors                        # 个别文件出错不中断，正常退出
)

if [ "$SHOW_PROGRESS" = true ]; then
    RSYNC_OPTS+=(--progress)
fi

if [ -n "$DRY_RUN" ]; then
    RSYNC_OPTS+=("$DRY_RUN")
fi

# 排除规则
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    RSYNC_OPTS+=(--exclude="$pattern")
done

# 可选：包含 .git
if [ "$INCLUDE_GIT" = false ]; then
    RSYNC_OPTS+=(--exclude=".git/")
fi

# 源目录尾部加 / 表示拷贝目录内容而非目录本身
SRC_RSYNC="${SRC%/}/"

# ---------- 执行 ----------
echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  双向同步工具${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "  方向:      ${GREEN}$DIRECTION${NC}"
echo -e "  源:        ${SRC_RSYNC}${NC}"
echo -e "  目标:      ${DST}${NC}"
echo -e "  排除 .git: ${INCLUDE_GIT}${NC}"
if [ -n "$DRY_RUN" ]; then
    echo -e "  模式:      ${YELLOW}预览 (dry-run)${NC}"
fi
echo ""

# 如果目标目录不存在则创建
if [ ! -d "$DST" ]; then
    echo -e "${YELLOW}[提示] 目标目录不存在，正在创建...${NC}"
    mkdir -p "$DST"
fi

# 执行 rsync
echo -e "${GREEN}开始同步...${NC}"
echo ""

START_TS=$(date +%s)

echo -e "${YELLOW}\$ rsync ${RSYNC_OPTS[*]} $SRC_RSYNC $DST${NC}"
EXIT_CODE=0
rsync "${RSYNC_OPTS[@]}" "$SRC_RSYNC" "$DST" || EXIT_CODE=$?

END_TS=$(date +%s)
ELAPSED=$((END_TS - START_TS))

echo ""
if [ $EXIT_CODE -eq 23 ]; then
    echo -e "${GREEN}同步完成（个别属性未写入 NTFS，数据已完整）${NC}"
elif [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}同步失败 (exit code $EXIT_CODE)${NC}"
    exit $EXIT_CODE
else
    echo -e "${GREEN}同步完成！${NC}"
fi
echo -e "  耗时: ${ELAPSED} 秒"

# ---------- 排除规则汇总 ----------
echo ""
echo -e "${CYAN}已排除的目录/文件类型:${NC}"
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    echo "  • $pattern"
done
if [ "$INCLUDE_GIT" = false ]; then
    echo "  • .git/"
fi
echo ""
