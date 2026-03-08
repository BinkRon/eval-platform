# 评测平台 — 问题与需求池

> 持续维护的问题追踪文档。记录设计评审、测试、用户反馈中发现的所有待改进项。
> 最后更新：2026-03-08

---

## 使用说明

### ID 规则

`{分类缩写}-{序号}`，序号在分类内自增，不跨分类复用。

| 缩写 | 分类 | 覆盖范围 |
|------|------|---------|
| UX | 产品与体验 | 用户流程、交互设计、信息展示、引导 |
| AR | 架构 | 分层违规、模式不一致、扩展性 |
| DM | 数据模型 | 表结构、字段设计、数据一致性 |
| SE | 安全 | 认证、加密、注入、信息泄露 |
| EN | 工程质量 | 代码规范、类型、废代码、测试 |
| PF | 性能 | 查询优化、并发、资源占用 |
| FT | 新功能 | 尚未实现的产品需求或改进想法 |

### 优先级定义

| 级别 | 含义 | 行动 |
|------|------|------|
| P0 | 阻塞核心流程或有安全风险 | 当前迭代必须修复 |
| P1 | 影响体验或架构健康度 | 下一迭代优先安排 |
| P2 | 有改进价值但不紧急 | 按容量安排 |
| P3 | 锦上添花 | 有空再做 |

### 状态

`Open` → `In Progress` → `Done` / `Won't Fix`

### 条目格式

每条问题包含：**标题**、**优先级**、**状态**、**来源**、**描述**、**涉及文件**（可选）、**建议方案**（可选）。

---

## 仪表盘

| 分类 | P0 | P1 | P2 | P3 | 总计 |
|------|----|----|----|----|------|
| UX 产品与体验 | 1 | 3 | 3 | 1 | 8 |
| AR 架构 | 0 | 2 | 1 | 0 | 3 |
| DM 数据模型 | 1 | 0 | 1 | 0 | 2 |
| SE 安全 | 0 | 1 | 0 | 0 | 1 |
| EN 工程质量 | 0 | 0 | 3 | 0 | 3 |
| PF 性能 | 0 | 0 | 0 | 0 | 0 |
| FT 新功能 | 0 | 0 | 2 | 0 | 2 |
| **合计** | **2** | **6** | **10** | **1** | **19** |

---

## UX · 产品与体验

### UX-01 模型配置 Tab 无 Provider 时缺少引导

- **优先级**：P0
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：用户未在"设置 → 模型管理"配置 LLM Provider 的 API Key 时，模型配置 Tab 的模型下拉框为空，无任何提示。新用户无法理解为什么没有可选模型，也不知道去哪配置。
- **涉及文件**：`frontend/src/components/model-config/`、`frontend/src/pages/ProviderList.tsx`
- **建议方案**：下拉框为空时显示 Alert："尚未配置模型供应商，请先前往 [模型管理] 添加"，附带跳转链接。

### UX-02 新项目无步骤引导

- **优先级**：P1
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：新用户进入空项目后，面对 4 个 Tab 不知道从哪里开始。缺少步骤引导、配置检查清单或空状态提示。直接影响 H2（配置门槛）的验证。
- **建议方案**：在工作台顶部增加配置进度条或 checklist："1. 添加 Agent 版本 ✓ → 2. 添加测试用例 → 3. 配置裁判 → 4. 配置模型 → 5. 发起批测"。已完成的步骤标绿，点击可跳转对应 Tab。

### UX-03 批测前置校验失败时无跳转

- **优先级**：P1
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：发起批测时 6 个前置条件校验失败后，仅显示文字提示（如"请先添加测试用例"），没有提供跳转链接让用户一键定位到对应 Tab。
- **涉及文件**：`frontend/src/components/batch-test/CreateBatchModal.tsx`
- **建议方案**：错误提示改为可点击的链接，点击后切换到对应 Tab。

### UX-04 Agent 版本编辑时 Token 字段体验不佳

- **优先级**：P1
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：因安全原因后端不返回 `auth_token`，编辑时 token 字段总是空白。用户可能误以为 token 丢失，或不确定留空是否会清除已有 token。
- **涉及文件**：`frontend/src/components/agent-version/`、`backend/app/services/agent_version_service.py`
- **建议方案**：已配置 token 时显示 placeholder "已配置，留空表示不修改"；后端 update 时 token 为空则跳过更新。

### UX-05 对话气泡缺少轮次编号

- **优先级**：P2
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：批测详情页展开用例后，对话气泡没有轮次编号。12 轮以上的对话很长，难以定位裁判总结中提到的具体轮次。
- **涉及文件**：`frontend/src/components/batch-test/ConversationBubbles.tsx`
- **建议方案**：每轮对话左侧增加轮次编号（如 "R1"、"R2"）。

### UX-06 裁判总结需要滚过整段对话才能看到

- **优先级**：P2
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：裁判总结放在对话记录下方，用户需要滚过完整对话才能看到。对话长时体验差。
- **建议方案**：将裁判总结移到对话记录上方，或做成可折叠的独立区域，默认展开。

### UX-07 项目列表空状态

- **优先级**：P2
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：新用户首屏是空的项目列表，没有引导文案。
- **建议方案**：空状态显示插图 + "创建你的第一个评测项目" + 新建按钮。

### UX-08 无 404 路由

- **优先级**：P3
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：前端 `App.tsx` 没有 catch-all 路由，访问不存在的路径显示空白 layout。
- **涉及文件**：`frontend/src/App.tsx`
- **建议方案**：添加 `*` 路由，渲染 404 页面或重定向到 `/projects`。

---

## AR · 架构

### AR-01 API 层架构不一致（部分路由缺 Service 层）

- **优先级**：P1
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：`projects` 和 `agent_versions` 已抽取 service 层，但 `test_cases`（create/update/delete）、`model_configs`、`providers` 的 CRUD 逻辑仍直接写在路由函数中，违反架构约定。
- **涉及文件**：`backend/app/api/test_cases.py`、`backend/app/api/model_configs.py`、`backend/app/api/providers.py`
- **建议方案**：为这三个资源分别创建 service 文件，路由层仅做参数解析和响应构造。

### AR-02 异常处理不统一

- **优先级**：P1
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：`test_cases.py`、`judge_configs.py`、`model_configs.py`、`providers.py` 仍直接 raise `HTTPException`，与 `main.py` 注册的领域异常处理器（`NotFoundError` → 404）模式不一致。
- **涉及文件**：同 AR-01 涉及文件 + `backend/app/api/judge_configs.py`
- **建议方案**：统一改为 raise 领域异常，由 main.py 的全局处理器转换为 HTTP 响应。与 AR-01 一起修复。

### AR-03 `ConflictError` 已注册但从未使用

- **优先级**：P2
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：`exceptions.py` 定义了 `ConflictError`，`main.py` 注册了 409 处理器，但代码中没有任何地方 raise 它。
- **涉及文件**：`backend/app/exceptions.py`、`backend/app/main.py`
- **建议方案**：在 provider 重名、项目重名等场景使用它；或确认不需要则移除。

---

## DM · 数据模型

### DM-01 批测不保存裁判配置快照

- **优先级**：P0
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：`test_results` 通过 `test_case_id` 关联用例，裁判结果直接存在 JSONB 字段中，但不保存批测时使用的裁判配置快照。用户修改裁判标准后查看历史批测，统计摘要区展示的 Checklist 条目可能与实际评判时的不一致，造成误解。
- **涉及文件**：`backend/app/models/batch_test.py`、`backend/app/services/batch_scheduler.py`
- **建议方案**：在 `batch_tests` 表增加 `judge_config_snapshot JSONB` 字段，批测创建时将当前裁判配置序列化存入。详情页展示时优先使用快照。

### DM-02 JudgeConfig 整体替换策略浪费 UUID

- **优先级**：P2
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：`judge_config_service.save_judge_config` 每次保存时删除所有 `checklist_items` 和 `eval_dimensions` 后重建。Schema 中 `ChecklistItemData.id` 声明了可选 UUID 但从未使用。频繁编辑产生大量废弃记录（虽然已级联删除，但 UUID 不可回收）。
- **涉及文件**：`backend/app/services/judge_config_service.py`、`backend/app/schemas/judge_config.py`
- **建议方案**：MVP 阶段影响不大，可保持现状。后续改为 diff 更新（有 id 则更新，无 id 则创建，多余的删除）。

---

## SE · 安全

### SE-01 敏感数据明文存储

- **优先级**：P1
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：`agent_versions.auth_token` 和 `provider_configs.api_key` 在数据库中明文存储。MVP 本地使用可接受，但上线前必须加密。
- **涉及文件**：`backend/app/models/agent_version.py`、`backend/app/models/provider_config.py`
- **建议方案**：使用对称加密（如 Fernet），密钥通过环境变量注入。写入时加密，读取时解密，API 层保持现有 `auth_token_set: bool` 模式不变。

---

## EN · 工程质量

### EN-01 `datetime.utcnow()` 已弃用

- **优先级**：P2
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：`batch_scheduler.py` 使用 `datetime.utcnow()`，该方法在 Python 3.12+ 已弃用。
- **涉及文件**：`backend/app/services/batch_scheduler.py`
- **建议方案**：替换为 `datetime.now(timezone.utc).replace(tzinfo=None)`（因 asyncpg 不接受 timezone-aware datetime 写入 `timestamp without time zone` 列）。

### EN-02 `LLMAdapter.chat_json()` 的 `json_schema` 参数无用

- **优先级**：P2
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：`base.py` 抽象方法声明了 `json_schema` 参数，但 `OpenAIAdapter` 和 `AnthropicAdapter` 都未使用它。
- **涉及文件**：`backend/app/llm/base.py`、`backend/app/llm/openai_adapter.py`、`backend/app/llm/anthropic_adapter.py`
- **建议方案**：移除该参数（当前无调用方传入），或在 OpenAI 适配器中实现 structured outputs 支持。

### EN-03 前端 `pass_threshold` 类型不匹配

- **优先级**：P2
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：后端 Pydantic 的 `Numeric` 类型序列化为字符串，前端 TypeScript 类型标注为 `number`，组件中用 `Number(config.pass_threshold)` 显式转换。类型声明与运行时行为不一致。
- **涉及文件**：`frontend/src/types/judgeConfig.ts`、`frontend/src/components/judge-config/JudgeConfigTab.tsx`
- **建议方案**：后端 schema 中对 `pass_threshold` 使用 `float` 类型（或添加 validator 转为 float），确保 JSON 序列化为数字而非字符串。

---

## PF · 性能

（暂无条目）

---

## FT · 新功能

### FT-01 批测结果删除功能

- **优先级**：P2
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：批测 API 没有 DELETE 端点。调试阶段会产生大量无效批测记录，无法清理。
- **建议方案**：增加 `DELETE /api/projects/:id/batch-tests/:bid`，级联删除关联的 `test_results`。

### FT-02 裁判一致性验证机制

- **优先级**：P2
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：Anthropic 适配器无原生 JSON mode，裁判输出稳定性依赖 prompt 工程。建议 MVP 验证阶段收集裁判一致性数据，以量化 H1 假设的可信度。
- **建议方案**：提供"重新评判"功能，对同一段对话再次调用裁判，对比两次结果的一致性。或在批测时自动对随机 N% 的用例做双重评判。

---

## 归档（已完成）

> 已修复的问题移到此处，保留记录。格式：`ID | 标题 | 完成日期 | 关联 commit`

（暂无）
