#!/bin/bash
# 远程发布脚本
# 用法：
#   ./deploy/release.sh
#   ./deploy/release.sh --ref master
#   ./deploy/release.sh --skip-pull
#   ./deploy/release.sh --skip-health

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
ENV_FILE="${PROJECT_DIR}/.env.production"
REF_NAME=""
SKIP_PULL=false
SKIP_HEALTH=false
ALLOW_DIRTY=false
HEALTH_RETRIES="${HEALTH_RETRIES:-20}"
HEALTH_INTERVAL="${HEALTH_INTERVAL:-3}"
BACKEND_HEALTH_URL="http://localhost:8000/api/health"
HEALTH_JSON_FILE=""
HEALTH_ERR_FILE=""

usage() {
    cat <<'EOF'
用法：
  ./deploy/release.sh [options]

选项：
  --ref <name>       指定发布的分支、tag 或 commit（默认：当前分支）
  --skip-pull        跳过 git fetch/pull，直接重建容器
  --skip-health      跳过健康检查
  --allow-dirty      允许服务器工作区存在未提交修改
  -h, --help         显示帮助

环境变量：
  HEALTH_RETRIES     健康检查最大重试次数（默认 20）
  HEALTH_INTERVAL    健康检查重试间隔秒数（默认 3）
EOF
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

die() {
    log "ERROR: $*"
    exit 1
}

cleanup() {
    [ -n "$HEALTH_JSON_FILE" ] && rm -f "$HEALTH_JSON_FILE"
    [ -n "$HEALTH_ERR_FILE" ] && rm -f "$HEALTH_ERR_FILE"
}

trap cleanup EXIT

read_env_value() {
    local key="$1"
    local default_value="${2:-}"
    local value=""

    if [ -f "$ENV_FILE" ]; then
        value="$(grep "^${key}=" "$ENV_FILE" | tail -n 1 | cut -d= -f2- | tr -d '[:space:]' || true)"
    fi

    if [ -n "$value" ]; then
        printf '%s\n' "$value"
    else
        printf '%s\n' "$default_value"
    fi
}

while [ $# -gt 0 ]; do
    case "$1" in
        --ref)
            [ $# -ge 2 ] || die "--ref 需要一个参数"
            REF_NAME="$2"
            shift 2
            ;;
        --skip-pull)
            SKIP_PULL=true
            shift
            ;;
        --skip-health)
            SKIP_HEALTH=true
            shift
            ;;
        --allow-dirty)
            ALLOW_DIRTY=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "未知参数: $1"
            ;;
    esac
done

cd "$PROJECT_DIR"

[ -f "$COMPOSE_FILE" ] || die "未找到生产 compose 文件: $COMPOSE_FILE"
[ -f "$ENV_FILE" ] || die "未找到环境变量文件: $ENV_FILE"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
else
    die "未找到 docker compose 或 docker-compose"
fi

run_compose() {
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"
}

if ! command -v git >/dev/null 2>&1; then
    die "未找到 git"
fi

if ! command -v docker >/dev/null 2>&1; then
    die "未找到 docker"
fi

if [ "$ALLOW_DIRTY" != "true" ]; then
    if [ -n "$(git status --short)" ]; then
        die "检测到服务器工作区存在未提交修改。请先提交/清理，或使用 --allow-dirty"
    fi
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
SYMBOLIC_BRANCH="$(git symbolic-ref -q --short HEAD || true)"
TARGET_REF="$CURRENT_BRANCH"
if [ -n "$REF_NAME" ]; then
    TARGET_REF="$REF_NAME"
fi

if [ -z "$REF_NAME" ] && [ -z "$SYMBOLIC_BRANCH" ]; then
    die "当前仓库处于 detached HEAD，无法默认发布。请先切回分支，或使用 --ref <branch|tag|commit>"
fi

log "项目目录: $PROJECT_DIR"
log "发布目标: $TARGET_REF"
log "Compose 命令: ${COMPOSE_CMD[*]}"

if [ "$SKIP_PULL" != "true" ]; then
    log "获取远程最新代码..."
    git fetch --all --tags

    if [ -n "$REF_NAME" ]; then
        if git show-ref --verify --quiet "refs/heads/$REF_NAME"; then
            git checkout "$REF_NAME"
            git pull --ff-only origin "$REF_NAME"
        elif git show-ref --verify --quiet "refs/tags/$REF_NAME"; then
            git checkout "tags/$REF_NAME"
        else
            git checkout "$REF_NAME"
        fi
    else
        git pull --ff-only
    fi
else
    log "已跳过 git pull"
fi

log "当前版本:"
git log --oneline -1

log "重建并启动生产容器..."
run_compose up -d --build

log "容器状态:"
run_compose ps

if [ "$SKIP_HEALTH" = "true" ]; then
    log "已跳过健康检查"
    exit 0
fi

log "等待 backend 健康检查通过..."
HEALTH_JSON_FILE="$(mktemp /tmp/eval_release_health.XXXXXX.json)"
HEALTH_ERR_FILE="$(mktemp /tmp/eval_release_health.XXXXXX.err)"
FRONTEND_PORT="$(read_env_value FRONTEND_PORT 80)"
i=1
while [ "$i" -le "$HEALTH_RETRIES" ]; do
    if run_compose exec -T backend curl -fsS "$BACKEND_HEALTH_URL" >"$HEALTH_JSON_FILE" 2>"$HEALTH_ERR_FILE"; then
        if curl -fsS "http://127.0.0.1:${FRONTEND_PORT}/" >/dev/null 2>&1; then
            log "backend 健康检查通过: $(tr -d '\n' <"$HEALTH_JSON_FILE")"
            log "frontend 入口检查通过: http://127.0.0.1:${FRONTEND_PORT}/"
            log "发布完成"
            exit 0
        fi
        log "backend 已就绪，但 frontend 入口暂不可访问: http://127.0.0.1:${FRONTEND_PORT}/"
    fi

    log "健康检查未通过，第 ${i}/${HEALTH_RETRIES} 次重试..."
    sleep "$HEALTH_INTERVAL"
    i=$((i + 1))
done

log "健康检查失败，最近日志如下："
run_compose logs --tail=80 backend
die "发布后健康检查失败"
