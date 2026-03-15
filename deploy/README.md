# 部署指南

## 环境要求

- CentOS/Rocky Linux 8+（或其他支持 Docker 的 Linux）
- Docker 24+、Docker Compose v2+
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

**必须修改：**

| 变量 | 说明 | 生成方法 |
|------|------|---------|
| `POSTGRES_PASSWORD` | 数据库密码 | 自定义强密码 |
| `EVAL_ENCRYPTION_KEY` | Fernet 加密密钥，保护 API Key 和 Auth Token | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `EVAL_JWT_SECRET` | JWT 签名密钥，用于用户认证 | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `EVAL_ADMIN_PASSWORD` | 管理员初始密码 | 自定义（见下方说明） |

**可选修改：**
- `EVAL_CORS_ORIGINS` — 实际访问地址，JSON 数组格式（如 `["http://192.168.1.100"]`）
- `FRONTEND_PORT` — 默认 80，如有冲突可改

> **关于管理员账号：** 首次启动时，数据库迁移会自动创建用户名为 `admin` 的管理员账号，密码取自 `EVAL_ADMIN_PASSWORD`。迁移只执行一次，之后该环境变量不再使用。如需修改密码，目前需通过数据库操作（暂无修改密码 UI）。

### 3. 启动服务

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

首次启动会自动创建数据库、运行 Alembic 迁移、启动后端和前端。

### 4. 验证

```bash
# 检查服务状态
docker compose -f docker-compose.prod.yml --env-file .env.production ps

# 健康检查
docker compose -f docker-compose.prod.yml --env-file .env.production exec backend curl -s http://localhost:8000/api/health

# 查看后端日志
docker compose -f docker-compose.prod.yml --env-file .env.production logs backend
```

打开浏览器访问前端页面，使用 `admin` / 你设置的密码 登录。

### 5. 防火墙放行

```bash
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --reload
```

---

## 更新部署

### 常规更新

```bash
cd /opt/eval-platform
git pull
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

数据库迁移会在 backend 启动时自动执行。数据存储在 Docker 命名卷 `pgdata` 中，`git pull` 和容器重建不会影响数据。

> **注意：** 如果更新引入了新的必填环境变量，需先更新 `.env.production`，否则后端会启动失败。对照 `.env.production.example` 检查是否有新增变量。

也可以使用脚本化发布（自动检查环境、拉代码、构建、健康检查）：

```bash
chmod +x deploy/release.sh
./deploy/release.sh
```

常用参数：`--ref <commit>` 发布指定版本、`--skip-pull` 跳过拉取、`--allow-dirty` 允许未提交修改、`--skip-health` 跳过健康检查。

### 版本升级说明

#### v1.0 → v1.1（账号系统 + 数据加密）

此版本引入了用户认证和敏感数据加密。

**1. 在 `.env.production` 中新增 3 个必填变量：** `EVAL_ENCRYPTION_KEY`、`EVAL_JWT_SECRET`、`EVAL_ADMIN_PASSWORD`（生成方法见上方表格）

**2. 重新构建并启动容器。** 启动时 Alembic 会自动执行两个迁移：
- `0005`：将数据库中现有的明文 API Key / Auth Token 加密
- `0006`：创建 users 表、插入 admin 种子账号、给 projects 表添加 owner_id

所有现有项目会自动归到 admin 账号名下，数据完全保留。

**3. 登录：** 用户名 `admin`，密码为 `EVAL_ADMIN_PASSWORD` 中设置的值。

---

## 日常运维

### 查看日志

```bash
# 所有服务
docker compose -f docker-compose.prod.yml --env-file .env.production logs -f

# 单个服务
docker compose -f docker-compose.prod.yml --env-file .env.production logs -f backend
```

### 重启 / 停止

```bash
# 重启
docker compose -f docker-compose.prod.yml --env-file .env.production restart

# 停止（不加 -v，数据库数据会保留）
docker compose -f docker-compose.prod.yml --env-file .env.production down
```

### 回滚

```bash
cd /opt/eval-platform
git log --oneline -5
./deploy/release.sh --ref <上一个稳定提交>
```

注意：回滚前确认是否包含数据库迁移。若已执行破坏性 migration，需提前设计数据库回滚方案。

---

## 数据库备份

### 自动备份（推荐）

```bash
sudo mkdir -p /data/backups/eval-platform

# 添加 cron 任务（每天凌晨 3 点）
crontab -e
# 添加：
0 3 * * * /opt/eval-platform/deploy/backup.sh >> /var/log/eval-backup.log 2>&1
```

### 手动备份 / 恢复

```bash
# 备份
./deploy/backup.sh

# 恢复
gunzip backup_20260310_030000.sql.gz
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T db \
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
| 启动报 RuntimeError | 检查 `.env.production` 中 `EVAL_ENCRYPTION_KEY` / `EVAL_JWT_SECRET` 是否已设置 |
