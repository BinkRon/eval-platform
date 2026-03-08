# 评测平台 — 架构设计

> 本文档描述项目的技术架构。随开发过程持续更新。
> 最后更新：2026-03-06

---

## 技术选型

| 层面 | 选择 | 理由 |
|------|------|------|
| 后端框架 | FastAPI | Python 异步框架，自带 OpenAPI 文档，适合并发对话调度 |
| 数据库 | PostgreSQL | JSONB 支持好（存对话记录），本地 Docker 运行，上云无缝迁移 |
| ORM | SQLAlchemy 2.0 + Alembic | Python 标准 ORM + 数据库迁移 |
| 前端框架 | React + TypeScript + Vite | 需求文档确定 |
| UI 组件库 | Ant Design | 表格、表单、弹窗丰富，适合后台管理类产品 |
| 前端状态 | TanStack Query | 服务端状态缓存、轮询、重新获取 |
| 前端路由 | React Router v6 | React 生态标准 |
| 本地开发 | Docker Compose | 一键启动 PostgreSQL + 后端 + 前端 |

---

## 目录结构

```
eval-platform/
├── CLAUDE.md                      # 项目入口文档
├── docs/                          # 产品 + 技术文档
│   ├── eval-platform-mvp-spec.md  # MVP 需求文档
│   ├── architecture.md            # 本文档
│   ├── conventions.md             # 代码规范
│   ├── progress.md                # 开发进度
│   ├── testing.md                 # 测试指南
│   └── archive/                   # 归档文档（产品愿景、跨项目规划）
│       ├── eval-platform-framework.md
│       └── project-roadmap.md
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI 入口
│   │   ├── config.py              # 配置管理（Pydantic Settings）
│   │   ├── database.py            # 数据库连接、AsyncSession
│   │   ├── models/                # SQLAlchemy 数据模型
│   │   ├── schemas/               # Pydantic 请求/响应模型
│   │   ├── api/                   # 路由处理（每个资源一个文件）
│   │   ├── services/              # 核心业务逻辑
│   │   ├── llm/                   # LLM 适配层
│   │   └── utils/                 # 工具函数
│   ├── alembic/                   # 数据库迁移
│   ├── tests/                     # 后端测试
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx               # React 入口
│   │   ├── App.tsx                # 路由配置
│   │   ├── pages/                 # 页面组件
│   │   ├── components/            # 业务组件（按模块分子目录）
│   │   ├── api/                   # API 调用层
│   │   ├── hooks/                 # 自定义 hooks
│   │   └── types/                 # TypeScript 类型定义
│   ├── vite.config.ts
│   └── package.json
├── docker-compose.yml
└── .claude/                       # Claude Code 配置
    ├── agents/                    # 审查 Agent
    ├── skills/                    # 自动化技能
    └── hooks/                     # Hook 脚本
```

---

## 数据库设计

### 实体关系

```
Project（项目）
  ├─ has many → AgentVersion（Agent 版本）
  ├─ has many → TestCase（测试用例）
  ├─ has one  → JudgeConfig（裁判配置）
  │                ├─ has many → ChecklistItem（检查项）
  │                └─ has many → EvalDimension（评判维度）
  ├─ has one  → ModelConfig（模型配置）
  └─ has many → BatchTest（批测）
                   └─ has many → TestResult（用例结果）

ProviderConfig（LLM 厂商配置）— 全局，不属于任何项目
```

### 表结构

```
projects
  id UUID PK, name VARCHAR(100), description TEXT,
  created_at TIMESTAMP, updated_at TIMESTAMP

agent_versions
  id UUID PK, project_id FK→projects, name VARCHAR(100),
  description TEXT, endpoint VARCHAR(500), method VARCHAR(10),
  auth_type VARCHAR(20), auth_token VARCHAR(500),
  request_template TEXT, response_path VARCHAR(200),
  has_end_signal BOOLEAN, end_signal_path VARCHAR(200), end_signal_value VARCHAR(100),
  connection_status VARCHAR(20), created_at, updated_at

test_cases
  id UUID PK, project_id FK→projects, name VARCHAR(100),
  first_message TEXT, persona_background TEXT, persona_behavior TEXT,
  max_rounds INTEGER(20), sort_order INTEGER, created_at, updated_at

judge_configs  -- 一个项目一条
  id UUID PK, project_id FK→projects(UNIQUE),
  pass_threshold DECIMAL(2,1)(2.0), created_at, updated_at

checklist_items
  id UUID PK, judge_config_id FK→judge_configs,
  content TEXT, level VARCHAR(20), sort_order INTEGER

eval_dimensions
  id UUID PK, judge_config_id FK→judge_configs,
  name VARCHAR(50), description TEXT,
  level_3_desc TEXT, level_2_desc TEXT, level_1_desc TEXT, sort_order INTEGER

model_configs  -- 一个项目一条
  id UUID PK, project_id FK→projects(UNIQUE),
  sparring_provider VARCHAR(50), sparring_model VARCHAR(100),
  sparring_temperature DECIMAL, sparring_max_tokens INTEGER, sparring_system_prompt TEXT,
  judge_provider VARCHAR(50), judge_model VARCHAR(100),
  judge_temperature DECIMAL, judge_max_tokens INTEGER, judge_system_prompt TEXT,
  created_at, updated_at

provider_configs  -- 全局
  id UUID PK, provider_name VARCHAR(50)(UNIQUE),
  api_key VARCHAR(500), base_url VARCHAR(500),
  available_models JSONB, is_active BOOLEAN, created_at, updated_at

batch_tests
  id UUID PK, project_id FK→projects, agent_version_id FK→agent_versions,
  status VARCHAR(20), concurrency INTEGER, total_cases INTEGER,
  passed_cases INTEGER, completed_cases INTEGER, created_at, completed_at

test_results
  id UUID PK, batch_test_id FK→batch_tests, test_case_id FK→test_cases,
  status VARCHAR(20), conversation JSONB, termination_reason VARCHAR(20),
  actual_rounds INTEGER, checklist_results JSONB, eval_scores JSONB,
  judge_summary TEXT, passed BOOLEAN, error_message TEXT, created_at, updated_at
```

### 级联删除规则

| 删除对象 | 级联行为 |
|---------|---------|
| Project | 删除所有 AgentVersion + TestCase + JudgeConfig(含子项) + ModelConfig + BatchTest(含 TestResult) |
| AgentVersion | 仅删除自身。关联的 BatchTest 保留（历史记录），agent_version_id 保留原值 |
| TestCase | 仅删除自身。关联的 TestResult 保留 |
| JudgeConfig | 级联删除 ChecklistItem + EvalDimension |
| BatchTest | 级联删除所有 TestResult |

---

## API 设计

```
# 全局模型管理
GET    /api/providers
POST   /api/providers
PUT    /api/providers/:pid
DELETE /api/providers/:pid
GET    /api/providers/models          # 所有可用模型（供下拉框）

# 项目
GET    /api/projects                  # 含最近批测摘要
POST   /api/projects
GET    /api/projects/:id
PUT    /api/projects/:id
DELETE /api/projects/:id
GET    /api/projects/:id/readiness      # 配置就绪状态检查

# Agent 版本
GET    /api/projects/:id/agent-versions
POST   /api/projects/:id/agent-versions
PUT    /api/projects/:id/agent-versions/:vid
DELETE /api/projects/:id/agent-versions/:vid
POST   /api/projects/:id/agent-versions/:vid/test

# 测试用例
GET    /api/projects/:id/test-cases
POST   /api/projects/:id/test-cases
PUT    /api/projects/:id/test-cases/:tid
DELETE /api/projects/:id/test-cases/:tid

# 裁判配置
GET    /api/projects/:id/judge-config
PUT    /api/projects/:id/judge-config   # 整体保存（含子项）

# 模型配置
GET    /api/projects/:id/model-config
PUT    /api/projects/:id/model-config

# 批测
GET    /api/projects/:id/batch-tests
POST   /api/projects/:id/batch-tests
GET    /api/projects/:id/batch-tests/:bid
GET    /api/projects/:id/batch-tests/:bid/progress
```

---

## 核心引擎

### LLM 适配层 (`app/llm/`)

```python
class LLMAdapter(ABC):
    async def chat(self, messages, system_prompt, temperature, max_tokens) -> str
    async def chat_json(self, messages, system_prompt, temperature, max_tokens, json_schema) -> dict
```

工厂方法根据 provider_name 创建适配器，从 provider_configs 读取 API Key。

### Agent Client (`services/agent_client.py`)

调用被测 Agent 的 HTTP 客户端。用 request_template 替换变量，httpx 发请求，jsonpath-ng 解析响应。

### Sparring Runner (`services/sparring_runner.py`)

对练运行器，最核心的服务。管理对话循环：首轮发言 → Agent 回复 → 检查终止 → 对练模型生成下一句 → 循环。

### Judge Runner (`services/judge_runner.py`)

裁判运行器。组装 prompt（system prompt + checklist + evaluation + 对话记录 + JSON schema），调用 LLM，解析结构化输出，计算通过判定。

### Batch Scheduler (`services/batch_scheduler.py`)

批测调度器。asyncio.Semaphore 控制并发，为每个用例执行 Sparring → Judge → 写入结果。

---

## 前端架构

### 路由

```
/                                → 重定向到 /projects
/projects                        → P1 项目列表页
/projects/:id                    → P2 项目工作台（Tab 容器）
/projects/:id?tab=...            → 各 Tab 内容
/projects/:id/batch-tests/:bid   → P3 批测详情页
/settings/providers              → 全局模型管理
```

### 状态管理

- 服务端状态：TanStack Query（缓存、轮询、乐观更新）
- 本地 UI 状态：React useState / useContext
- 批测进度：TanStack Query 的 refetchInterval（3 秒轮询）

---

## 关键技术决策

| 决策 | 选择 | 替代方案 | 理由 |
|------|------|---------|------|
| 任务队列 | asyncio.Semaphore | Celery + Redis | MVP 用户量小，无额外依赖 |
| 批测进度 | 前端轮询 | WebSocket / SSE | 实现简单，体验够用 |
| 裁判输出 | LLM JSON mode + 重试 | 正则提取 | 更可靠 |
| 用户认证 | MVP 暂不做 | JWT / OAuth | 小团队试用不需要 |
| 对话存储 | JSONB 字段 | 独立对话表 | MVP 查询需求简单 |
| 前端状态 | TanStack Query | Redux / Zustand | 主要是服务端状态 |
