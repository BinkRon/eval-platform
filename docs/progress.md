# 评测平台 — 开发进度

## v1.1 安全 + 认证 + 体验打磨（进行中）

> 核心目标：**部署到公司服务器的前提**（加密 + 认证）+ **API 专业度**（自描述）+ **体验打磨**
> 覆盖需求：SE-01 / FT-05 / EN-05 / UX-13 / UX-11 / FT-04

---

### Phase 1：SE-01 敏感数据加密

> Fernet 对称加密，写入加密 + 读取解密 + 存量数据迁移

- [x] **1-1：加密工具模块** `[S]`
  - 新建 `backend/app/utils/crypto.py` — Fernet encrypt/decrypt，启动时 init_fernet
  - `config.py` 新增 encryption_key / jwt_secret / jwt_expire_minutes / admin_password
  - `pyproject.toml` 添加 cryptography / pyjwt / bcrypt
- [x] **1-2：写入路径加密** `[S]`
  - `agent_version_service` create/update：encrypt auth_token
  - `provider_service` create/update：encrypt api_key
- [x] **1-3：读取路径解密** `[S]`
  - `agent_version_service.test_connection` — 解密 auth_token
  - `batch_scheduler._load_context` — 解密 sparring/judge api_key + agent auth_token
  - `builder_agent_service._get_llm_adapter` — 解密 api_key
- [x] **1-4：数据迁移** `[M]`
  - `0005_encrypt_sensitive_data.py` — 遍历现有明文，Fernet 加密回写；downgrade 解密
- [x] **1-5：测试** `[S]`
  - `test_crypto.py` — 10 个测试（往返、不同密文、空值、unicode、无效 key、未初始化）

**验证**：pytest 105 passed ✓

---

### Phase 2：FT-05 账号系统

> JWT 认证强制启用 + 管理员种子账号 + 按 owner 隔离数据

- [x] **2-1：User 模型 + 迁移** `[M]`
  - `models/user.py` — username/email/password_hash/is_active/role
  - `0006_add_users_and_project_owner.py` — 创建 users 表 + admin 种子 + projects.owner_id 回填
  - `models/project.py` 新增 owner_id FK
- [x] **2-2：Auth Schemas** `[S]`
  - `schemas/auth.py` — RegisterRequest / LoginRequest / TokenResponse / UserResponse（含 description）
- [x] **2-3：Auth Service** `[M]`
  - `services/auth_service.py` — register / login / verify_token / bcrypt 哈希
- [x] **2-4：Auth 依赖 + 异常** `[M]`
  - `dependencies.py` — get_current_user（从 Bearer token 提取 JWT）
  - `exceptions.py` 新增 AuthenticationError → `main.py` 401 处理器
- [x] **2-5：Auth API 路由** `[S]`
  - `api/auth.py` — POST register / POST login / GET me
- [x] **2-6：保护现有路由 + 数据隔离** `[M]`
  - 10 个路由文件添加 `Depends(get_current_user)`
  - `project_service.py` — list/create/get/update/delete 全部按 owner_id 隔离
- [x] **2-7：前端登录 + Token 管理** `[M]`
  - LoginPage / RegisterPage / utils/auth.ts / types/auth.ts / api/auth.ts / hooks/useAuth.ts
  - `api/client.ts` 请求拦截器加 Bearer + 401 跳转 /login
- [x] **2-8：前端路由守卫 + 用户菜单** `[S]`
  - `AuthGuard.tsx` — 无 token 跳 /login
  - `App.tsx` — /login + /register 在 MainLayout 外
  - `MainLayout.tsx` — Sider 底部用户名 + 退出按钮
- [x] **2-9：测试** `[M]`
  - `test_auth_service.py` — 注册成功/重名/登录成功/密码错误/JWT 有效/过期/篡改

**验证**：pytest 115 passed ✓ + tsc --noEmit ✓

---

### Phase 3：EN-05 API 自描述补全

> Schema descriptions + 路由 docstrings → OpenAPI 文档完整

- [ ] **3-1：Pydantic Schema descriptions** `[M]`
  - 9 个 schema 文件：所有 Field 加 description + Schema 类加 docstring + 关键字段加 examples
- [ ] **3-2：FastAPI 路由 docstrings** `[M]`
  - 10 个 API 路由文件：每个路由函数加中文 docstring

**验证**：pytest 通过 + tsc --noEmit 通过 + `/docs` 描述完整

---

### Phase 4：UX + FT 小修

> 4 个独立修复点

- [ ] **4-1：UX-13 System Prompt 展开/收起** `[S]`
  - `ModelConfigTab.tsx` — expandable collapsible + 展开/收起 symbol
- [ ] **4-2：UX-11 添加按钮移到标题区** `[S]`
  - `AgentVersionTab.tsx` + `TestCaseTab.tsx` — flex 标题行（左标题 + 右按钮）
- [ ] **4-3：FT-04 Provider 连通性测试** `[M]`
  - 后端 `provider_service.test_connection` + `POST /api/providers/{id}/test` + ProviderTestResult
  - 前端 ProviderSettings 操作列加"测试连接"
- [ ] **4-4：FT-04 Agent 版本 Modal 内测试** `[S]`
  - 后端 `POST .../agent-versions/test-unsaved` + test_connection_unsaved
  - 前端 AgentVersionTab Modal footer 加"测试连接"

**验证**：tsc --noEmit 通过 + pytest 通过

---

### Phase 5：文档收尾

- [ ] 更新 `docs/architecture.md` — User 模型 / auth API / 加密方案
- [ ] 更新 `docs/conventions.md` — auth / 加密约定
- [ ] 更新 `docs/backlog.md` — 6 条标记 Done + 归档
- [ ] 更新 `CLAUDE.md` — 版本号 v1.1

---

## 交接备注

**Session #36 (2026-03-14)**：Phase 1-2 审查修复 + 部署配置 + 文档整理。

- 审查修复：8 个子资源路由统一用 `verify_project_access`；ORM 解密用 SimpleNamespace 代理；启动校验 encryption_key/jwt_secret；迁移要求 EVAL_ADMIN_PASSWORD；register 兜底 IntegrityError；AuthGuard 处理 isError；前端硬编码颜色替换为 SEMANTIC_COLORS
- 部署配置：docker-compose 补 3 个安全变量；创建本地 `.env`；跑完 0005+0006 迁移；后端重启验证通过
- 文档整理：`deploy/README.md` 精简（460→150 行），补管理员账号机制说明；backlog 状态同步
- 下一步：Phase 3（EN-05 API 自描述补全）

**Session #35 (2026-03-14)**：v1.1 Phase 1-2 编码。

- Phase 1：Fernet 加密工具 + 写入/读取路径 + 数据迁移 `0005` + 10 个测试
- Phase 2：User 模型 + JWT auth + 10 路由保护 + project 数据隔离 + 前端登录/注册/守卫
- 依赖变更：+cryptography +pyjwt +bcrypt，弃用 passlib（与新版 bcrypt 不兼容）

**Session #34 (2026-03-14)**：暖绿主题迁移（Humanloop 风格）。

- 新建 `frontend/src/theme/themeConfig.ts` — 集中定义 Ant Design token + SEMANTIC_COLORS 语义色常量
- 布局从顶部深色 Header 迁移至左侧固定 Sider（232px，暖奶油底色）
- 全局色彩：森林绿主色 `#2d7a4e` + 暖奶油底色 `#f3f1ec`，无紫色元素
- 修复 Sider flex+overflow 冲突、Tag 标签对比度
- conventions.md 新增前端样式规范

<details>
<summary>v1.0 二期功能实现（已完成） — Phase 1-7，Session #26-#33</summary>

> PRD：`docs/prd/eval-platform-phase2-spec.md`
> 核心：构建 Agent（AI 辅助配置）+ 数据模型简化 + Prompt 组装重构

- **Phase 1**（5 任务 ✅）：数据模型迁移 — Alembic `0004` + TestCase/EvalDimension 字段重构 + ProjectFile/BuilderConversation 新表
- **Phase 2**（5 任务 ✅）：核心引擎适配 — SparringRunner/JudgeRunner 新字段注入 + 默认 System Prompt + 旧 snapshot 兼容
- **Phase 3**（4 任务 ✅）：前端适配 — TestCaseTab/JudgeConfigTab 简化 + ModelConfigTab 默认 Prompt 展示
- **Phase 4**（6 任务 ✅）：新增后端 API — 项目文件/构建对话/构建 Agent 聊天 + 文件解析器（73 tests）
- **Phase 5**（7 任务 ✅）：构建 Agent 前端 UI — 悬浮球 + 对话面板（Optimistic update）+ 确认卡片 + 文件管理 + ProjectLayout
- **Phase 6**（4 任务 ✅）：构建 Agent 智能层 — Skill 定义 + 结构化输出解析 + 配置写入（95 tests）
- **Phase 7**（8 任务 ✅）：文档 + Agent 守卫 + 收尾 — architecture/testing/conventions/backlog 全面更新

**Session #33**：文档体系 review + 修复 10 项。**Session #32**：Phase 7 完成。**Session #31**：Phase 6。**Session #30**：Phase 5。**Session #29**：Phase 4。**Session #28**：Phase 2+3。**Session #27**：Phase 1。**Session #26**：规划。

</details>

<details>
<summary>v0.3 稳定性与体验修复（已完成） — Phase BugFix + P1 + P2 + Deploy，Session #17-#25</summary>

- **Phase BugFix**（3 任务 ✅）：批测 running 恢复、对话剧场布局、模型配置引导
- **Phase P1**（5 任务 ✅）：批测删除、Service 层补全、Token 编辑、轮次编号、datetime 修复
- **Phase P2**（6 任务 ✅）：批测多选、裁判配置查看态、模型配置查看态、Agent Modal 分组、pass_threshold float、chat_json 清理
- **Phase Deploy**（7 任务 ✅）：Docker Compose 生产化、自动迁移、Nginx 加固、健康检查、备份脚本、部署文档、安全加固

</details>

<details>
<summary>v0.2 架构重构（已完成） — Phase 1-5 + UX，Session #9-#16</summary>

- **Phase 1-5 + UX**（29 任务 ✅）：页面下钻架构（P2 配置摘要 + P3 配置页 + P4 表格化 + P5 对话剧场）+ 端到端验收

</details>

<details>
<summary>v0.1 MVP（已完成） — Phase A-F，Session #1-#8</summary>

- **Phase A-F**：项目脚手架 + 数据管理 + 核心引擎 + 批测界面 + 补全打磨 + 质量加固

</details>
