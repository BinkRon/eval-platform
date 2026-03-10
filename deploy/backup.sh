#!/bin/bash
# 数据库定时备份脚本
# 用法: 通过 cron 定时执行，例如每天凌晨 3 点：
#   0 3 * * * /path/to/eval-platform/deploy/backup.sh >> /var/log/eval-backup.log 2>&1

set -euo pipefail

# 配置
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-/data/backups/eval-platform}"
KEEP_DAYS="${KEEP_DAYS:-7}"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"

# 从 .env.production 读取数据库配置（安全解析，不执行 shell 代码）
ENV_FILE="${PROJECT_DIR}/.env.production"
if [ -f "$ENV_FILE" ]; then
    DB_USER=$(grep '^POSTGRES_USER=' "$ENV_FILE" | cut -d= -f2- | tr -d '[:space:]')
    DB_NAME=$(grep '^POSTGRES_DB=' "$ENV_FILE" | cut -d= -f2- | tr -d '[:space:]')
fi

DB_USER="${DB_USER:-eval_user}"
DB_NAME="${DB_NAME:-eval_platform}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 确保备份目录存在
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

# 执行备份
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz"
docker compose -f "$COMPOSE_FILE" exec -T db \
    pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE" \
    || { rm -f "$BACKUP_FILE"; echo "[$(date)] Backup FAILED, partial file removed."; exit 1; }

echo "[$(date)] Backup saved: backup_${TIMESTAMP}.sql.gz"

# 清理过期备份
DELETED=$(find "$BACKUP_DIR" -name "*.sql.gz" -mtime +${KEEP_DAYS} -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "[$(date)] Cleaned up ${DELETED} old backup(s)"
fi

echo "[$(date)] Backup completed."
