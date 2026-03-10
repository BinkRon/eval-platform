# 部署指南

## 环境要求

- CentOS/Rocky Linux 8+
- Docker 24+
- Docker Compose v2+
- Git

### 安装 Docker（CentOS/Rocky）

```bash
sudo dnf install -y dnf-utils
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# 重新登录使 docker 组生效
```

---

## 首次部署

### 1. 拉取代码

```bash
cd /opt
git clone <你的仓库地址> eval-platform
cd eval-platform
```

### 2. 配置环境变量

```bash
cp .env.production.example .env.production
vim .env.production
```

必须修改：
- `POSTGRES_PASSWORD` — 设置强密码

可选修改：
- `EVAL_CORS_ORIGINS` — 填写实际访问地址（如 `http://192.168.1.100`）
- `FRONTEND_PORT` — 默认 80，如有冲突可改

### 3. 启动服务

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

首次启动会自动：
- 创建 PostgreSQL 数据库
- 运行 Alembic 迁移
- 启动后端和前端

### 4. 验证

```bash
# 检查服务状态
docker compose -f docker-compose.prod.yml ps

# 检查健康状态（通过容器内部访问）
docker compose -f docker-compose.prod.yml exec backend curl -s http://localhost:8000/api/health

# 查看后端日志
docker compose -f docker-compose.prod.yml logs backend
```

### 5. 防火墙放行

```bash
# 放行前端端口（默认 80）
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --reload
```

---

## 日常运维

### 更新部署

```bash
cd /opt/eval-platform
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

数据库迁移会在 backend 启动时自动执行。

### 查看日志

```bash
# 所有服务
docker compose -f docker-compose.prod.yml logs -f

# 单个服务
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f db
```

### 重启服务

```bash
# 重启所有
docker compose -f docker-compose.prod.yml restart

# 重启单个
docker compose -f docker-compose.prod.yml restart backend
```

### 停止服务

```bash
docker compose -f docker-compose.prod.yml down
# 注意：不加 -v 参数，数据库数据会保留
```

---

## 数据库备份

### 配置自动备份

```bash
# 创建备份目录
sudo mkdir -p /data/backups/eval-platform

# 添加 cron 任务（每天凌晨 3 点）
crontab -e
# 添加以下行：
0 3 * * * /opt/eval-platform/deploy/backup.sh >> /var/log/eval-backup.log 2>&1
```

### 手动备份

```bash
cd /opt/eval-platform
./deploy/backup.sh
```

### 恢复备份

```bash
# 解压备份文件
gunzip backup_20260310_030000.sql.gz

# 恢复到数据库
docker compose -f docker-compose.prod.yml exec -T db \
    psql -U eval_user eval_platform < backup_20260310_030000.sql
```

---

## 故障排查

| 现象 | 排查方法 |
|------|---------|
| 前端访问不了 | `docker compose ps` 看容器状态，`firewall-cmd --list-ports` 看端口 |
| API 返回 502 | `docker compose logs backend` 看后端日志 |
| 数据库连不上 | `docker compose logs db` 看 PG 日志，检查 `.env.production` 密码 |
| 迁移失败 | `docker compose logs backend` 看 alembic 报错 |
