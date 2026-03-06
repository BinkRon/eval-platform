---
name: commit
description: 提交当前未 commit 的修改。自动分析变更内容，按模块分组提交，生成规范的中文 commit message。
---

# Git Commit 技能

提交当前未 commit 的修改到 git 仓库。

## 工作流程

### 步骤一：查看未提交修改

```bash
git status --short
```

分析变更类型：
- M - 已修改
- ?? - 新文件（未跟踪）
- D - 已删除
- R - 重命名

### 步骤二：分析变更内容

根据修改文件路径判断变更所属模块：

| 路径模式 | 模块 |
|----------|------|
| `backend/app/models/` | 数据模型层 |
| `backend/app/schemas/` | 请求/响应模型 |
| `backend/app/api/` | API 路由层 |
| `backend/app/services/` | 业务逻辑层 |
| `backend/app/llm/` | LLM 适配层 |
| `backend/alembic/` | 数据库迁移 |
| `backend/tests/` | 后端测试 |
| `backend/` | 后端（其他） |
| `frontend/src/pages/` | 前端页面 |
| `frontend/src/components/` | 前端组件 |
| `frontend/src/api/` | 前端 API 调用 |
| `frontend/src/hooks/` | 前端 Hooks |
| `frontend/src/types/` | 前端类型定义 |
| `frontend/` | 前端（其他） |
| `docs/` | 文档 |
| `CLAUDE.md` | 项目配置 |
| `.claude/` | Claude Code 配置 |
| 根目录配置文件 | 项目配置（docker-compose 等） |

### 步骤三：决定提交策略

**单一模块修改**：一次性提交所有文件。

**多模块修改**：按模块分组提交，优先级如下：

1. 文档变更（docs/、CLAUDE.md）— 合并为一个 commit
2. 数据库迁移（alembic/）— 单独 commit
3. 数据模型 + 请求模型（models/ + schemas/）— 合并为一个 commit
4. API 路由 + 业务逻辑（api/ + services/）— 按功能关联合并
5. LLM 适配层（llm/）— 单独 commit
6. 前端类型定义（types/）— 单独 commit
7. 前端页面 + 组件（pages/ + components/ + api/ + hooks/）— 按功能关联合并
8. 后端测试（tests/）— 单独 commit
9. 项目配置（docker-compose、.claude/ 等）— 合并为一个 commit

**判断关联性**：如果多个模块的变更是为了同一个功能（比如新增一个 API + 对应的前端页面），优先合并为一个 commit。

### 步骤四：生成 Commit Message

格式规范：
- 用中文
- 格式：`<类型>: <简洁描述>`
- 不超过 50 字

类型和模板：

| 场景 | 类型 | 示例 |
|------|------|------|
| 新增功能 | feat | `feat: 添加项目列表页` |
| 修复 bug | fix | `fix: 修复批测进度轮询不更新` |
| 重构 | refactor | `refactor: 重构 LLM 适配层接口` |
| 样式 | style | `style: 调整批测详情页布局` |
| 文档 | docs | `docs: 更新开发进度` |
| 配置 | chore | `chore: 配置 Docker Compose` |
| 数据库 | db | `db: 新增 eval_dimensions 表` |
| 测试 | test | `test: 补充裁判运行器单元测试` |

### 步骤五：执行提交

```bash
git add <file1> <file2> ...
git commit -m "commit message"
```

注意：
- **禁止使用** `git add .` 或 `git add -A`
- 明确指定要提交的文件
- 排除临时文件（*.pyc、__pycache__/、*.log）
- 排除 .DS_Store

### 步骤六：确认结果

```bash
git log --oneline -5
```

输出最近提交记录确认成功。

## 排除规则

以下文件默认不提交：
- `*.pyc` / `__pycache__/` — Python 编译缓存
- `*.log` — 日志文件
- `.DS_Store` — macOS 系统文件
- `node_modules/` — 前端依赖
- `dist/` — 前端构建产物
- `.venv/` / `venv/` — Python 虚拟环境
- `.env` — 环境变量（含敏感信息）
