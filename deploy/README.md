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
- `EVAL_CORS_ORIGINS` — 填写实际访问地址，JSON 数组格式（如 `["http://192.168.1.100"]`）
- `FRONTEND_PORT` — 默认 80，如有冲突可改

### 3. 启动服务

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

首次启动会自动：
- 创建 PostgreSQL 数据库
- 运行 Alembic 迁移
- 启动后端和前端

### 4. 验证

```bash
# 检查服务状态
docker compose -f docker-compose.prod.yml --env-file .env.production ps

# 检查健康状态（通过容器内部访问）
docker compose -f docker-compose.prod.yml --env-file .env.production exec backend curl -s http://localhost:8000/api/health

# 查看后端日志
docker compose -f docker-compose.prod.yml --env-file .env.production logs backend
```

### 5. 防火墙放行

```bash
# 放行前端端口（默认 80）
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --reload
```

---

## 日常运维

### 推荐工作流：本地开发 → 远程发布

目标：避免“本地验证通过，远程 Docker 跑出来却不一样”。

核心原则：
- 本地尽量也使用 Docker 验证，而不是只在宿主机裸跑
- 远程发布只做标准动作：拉代码、构建镜像、重启容器、检查健康状态
- 环境变量只允许“值不同”，不允许“字段缺失或语义不同”
- 数据库结构只通过 Alembic migration 变更，不手改线上库

### 一、开发环境约定

本地开发使用：

```bash
docker compose -f docker-compose.yml up -d --build
```

用途：
- 启动本地 PostgreSQL、backend、frontend
- 验证代码在容器环境内可以正常构建和运行

远程生产使用：

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

用途：
- 使用生产环境变量
- 使用生产端口、Nginx、健康检查、自动迁移

要求：
- 不要在本地只用宿主机 Python/Node 验证，然后直接发布到远程 Docker
- 至少在发布前跑一次本地 Docker 验证，确保运行环境接近生产

### 二、发布前标准检查

每次准备发布到远程服务器前，至少完成以下检查：

```bash
# 1) 后端关键测试（如本地环境已安装 pytest）
cd backend
pytest

# 2) 前端类型检查
cd ../frontend
npm ci
npm run build

# 3) 回到项目根目录，验证本地 Docker 能启动
cd ..
docker compose -f docker-compose.yml up -d --build

# 4) 健康检查
curl -s http://localhost:8000/api/health

# 5) 手动冒烟
# - 打开前端页面
# - 检查 Provider / 模型配置 / 用例 / 批测页面
# - 至少发起一轮单用例批测
```

推荐的最低冒烟标准：
- `/api/health` 返回 `{"status":"ok","database":"connected"}`
- Provider 可正常读取
- 模型配置可正常保存
- 发起一条单用例批测，状态能从 `pending/running` 进入 `completed/failed`
- 批测详情页能看到 conversation、termination_reason、judge_summary

### 三、发布流程（推荐）

#### 方案 A：当前项目的最简单流程

适合现在这个仓库，实施成本最低。

1. 本地完成开发和验证
2. 提交到 GitHub
3. 在远程服务器拉取最新代码
4. 使用生产 compose 重新构建并重启
5. 做线上冒烟验证

命令如下：

```bash
# 本地
git push origin master

# 远程服务器
cd /opt/eval-platform
git pull
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.production ps
docker compose -f docker-compose.prod.yml --env-file .env.production exec backend curl -s http://localhost:8000/api/health
```

发布完成后必须再做一次线上冒烟：
- 打开生产前端页面
- 检查项目列表是否正常
- 发起一轮单用例批测
- 确认后端日志没有新的报错

#### 方案 B：更稳的镜像化发布流程

适合后续把线上和本地效果进一步对齐。

原则：
- 本地构建镜像
- 本地先验证镜像
- 远程只拉同一个镜像 tag 并重启

好处：
- 本地和远程运行的是同一个镜像，不是“两边各自重新 build”
- 更容易排查“代码相同但环境不同”的问题

如果后续要升级到这套流程，建议增加：
- 镜像 tag 规范（如 commit sha 或日期版本号）
- 镜像仓库（Docker Hub / GHCR / 私有仓库）
- 发布脚本（pull + up -d）

### 四、如何保证本地和远程效果对齐

#### 1. 保持环境变量结构一致

当前仓库的真实约定是：
- 生产模板文件：`.env.production.example`
- 生产实际文件：`.env.production`
- 本地开发 compose 目前直接在 `docker-compose.yml` 中写死默认值

因此现阶段最重要的不是“强行维护三套同名 env 文件”，而是确保以下字段在本地理解和生产配置中的语义一致：
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `EVAL_CORS_ORIGINS`
- `EVAL_ALLOW_PRIVATE_URLS`
- `FRONTEND_PORT`
- `BACKEND_HOST`
- `BACKEND_PORT`

补充说明：
- 生产环境中的 `EVAL_DATABASE_URL` 不是直接写在 `.env.production` 里，而是由 `docker-compose.prod.yml` 使用 `POSTGRES_*` 变量拼出来
- 如果后续要进一步统一本地与生产配置，可以再补 `.env.local` 机制；当前版本先以 `.env.production.example` 为准

#### 2. 保持数据库版本一致

要求：
- 所有数据库变更必须提交 Alembic migration
- 本地先执行 migration 验证
- 远程通过 backend 启动时自动执行 `alembic upgrade head`

禁止：
- 手改线上表结构
- 本地改了 schema 但不补 migration

#### 3. 保持验证动作一致

本地验证什么，线上就复验什么。推荐固定一个“发布冒烟清单”：
- 健康检查通过
- Provider 可读
- 模型配置可读
- 单用例批测可运行
- 结果详情页可查看

#### 4. 禁止在线上容器里手改代码

线上容器只用于运行，不用于开发。

禁止长期做法：
- `docker exec` 进入容器改 Python 文件
- 容器里临时打补丁后不回写 Git

正确做法：
- 本地改代码
- Git 提交
- 远程重建容器

### 五、回滚策略

若发布后发现问题，优先使用“小回滚”：

```bash
cd /opt/eval-platform
git log --oneline -5
./deploy/release.sh --ref <上一个稳定提交或稳定 tag>
```

注意：
- 回滚代码前先确认是否包含数据库迁移
- 不要长期停留在 `git checkout <commit>` 的 detached HEAD 状态后再执行默认发布；恢复常规发布前，应切回分支，或显式使用 `./deploy/release.sh --ref master`
- 若已执行破坏性 migration，需提前设计数据库回滚方案
- 日常发布尽量保持“小步快跑”，每次改动范围小，回滚风险更低

### 更新部署

```bash
cd /opt/eval-platform
git pull
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

数据库迁移会在 backend 启动时自动执行。

更推荐使用脚本化发布：

```bash
cd /opt/eval-platform
chmod +x deploy/release.sh
./deploy/release.sh
```

脚本默认会执行：
- 检查 `.env.production` 和 `docker-compose.prod.yml` 是否存在
- 检查服务器工作区是否干净（默认不允许带未提交修改发布）
- `git fetch --all --tags`
- `git pull --ff-only`
- `docker compose ... up -d --build`
- 检查 backend 健康状态
- 检查 frontend 对外入口可访问

常用参数：

```bash
# 发布指定分支 / tag / commit
./deploy/release.sh --ref master

# detached HEAD / 回滚场景下，显式指定要发布的目标
./deploy/release.sh --ref <commit或tag>

# 已经手动 pull 过代码时，跳过拉取
./deploy/release.sh --skip-pull

# 临时允许服务器存在未提交修改（不推荐长期使用）
./deploy/release.sh --allow-dirty

# 跳过健康检查
./deploy/release.sh --skip-health
```

说明：
- 默认推荐直接执行 `./deploy/release.sh`
- 如果脚本失败，会打印最近的 backend 日志，便于排查
- 如果服务器较慢，可通过环境变量调整健康检查等待时间：

```bash
HEALTH_RETRIES=30 HEALTH_INTERVAL=5 ./deploy/release.sh
```

### 查看日志

```bash
# 所有服务
docker compose -f docker-compose.prod.yml --env-file .env.production logs -f

# 单个服务
docker compose -f docker-compose.prod.yml --env-file .env.production logs -f backend
docker compose -f docker-compose.prod.yml --env-file .env.production logs -f frontend
docker compose -f docker-compose.prod.yml --env-file .env.production logs -f db
```

### 重启服务

```bash
# 重启所有
docker compose -f docker-compose.prod.yml --env-file .env.production restart

# 重启单个
docker compose -f docker-compose.prod.yml --env-file .env.production restart backend
```

### 停止服务

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production down
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
