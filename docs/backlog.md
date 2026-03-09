# 评测平台 — 问题与需求池

> 持续维护的问题追踪文档。记录设计评审、测试、用户反馈中发现的所有待改进项。
> 最后更新：2026-03-09

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

### 复杂度定义

| 级别 | 含义 | 参考工作量 |
|------|------|-----------|
| S | 单文件小改动 | < 30 min |
| M | 多文件改动或前后端联动 | 1-3 h |
| L | 涉及架构调整或新增完整功能 | 半天以上 |

### 状态

| 状态 | 含义 | 说明 |
|------|------|------|
| `Open` | 已识别，未排期 | 在 backlog 中等待评估 |
| `Scheduled` | 已排入 Phase | 标注目标 Phase（如 "Scheduled → v0.3 BugFix"） |
| `In Progress` | 正在开发中 | 对应 progress.md 中的任务 |
| `Done` | 已完成并验证 | 待归档 |
| `Won't Fix` | 决定不做 | 附原因，直接归档 |

流转：`Open` → `Scheduled` → `In Progress` → `Done` / `Won't Fix`

### 与 progress.md 的关系

- **backlog.md**：需求池，所有已识别的问题和需求（含优先级、复杂度、来源）
- **progress.md**：执行计划，当前版本的 Phase 分解和开发进度
- 排期时：从 backlog 选取条目 → 标记为 `Scheduled` → 在 progress.md 中创建对应任务
- 完成时：progress.md 勾选 → backlog 标记 `Done` → 归档

### 条目格式

每条问题包含：**标题**、**优先级**、**复杂度**、**状态**、**来源**、**描述**、**涉及文件**（可选）、**建议方案**（可选）。

---

## 仪表盘

| 分类 | P0 | P1 | P2 | P3 | 总计 |
|------|----|----|----|----|------|
| UX 产品与体验 | 0 | 0 | 1 | 1 | 2 |
| AR 架构 | 0 | 0 | 0 | 0 | 0 |
| DM 数据模型 | 0 | 0 | 1 | 0 | 1 |
| SE 安全 | 0 | 1 | 0 | 0 | 1 |
| EN 工程质量 | 0 | 0 | 0 | 0 | 0 |
| PF 性能 | 0 | 0 | 0 | 0 | 0 |
| FT 新功能 | 0 | 0 | 2 | 0 | 2 |
| **合计** | **0** | **1** | **4** | **1** | **6** |

---

## UX · 产品与体验

### UX-01 模型配置页无 Provider 时缺少引导

- **优先级**：P0
- **复杂度**：S
- **状态**：Done
- **来源**：设计评审 2026-03-08
- **描述**：用户未在"设置 → 模型管理"配置 LLM Provider 的 API Key 时，模型配置区域的模型下拉框为空，无任何提示。新用户无法理解为什么没有可选模型，也不知道去哪配置。
- **涉及文件**：`frontend/src/components/model-config/ModelConfigTab.tsx`、`frontend/src/pages/ProviderSettings.tsx`
- **建议方案**：下拉框为空时显示 Alert："尚未配置模型供应商，请先前往 [模型管理] 添加"，附带跳转链接。

### UX-04 Agent 版本编辑时 Token 字段体验不佳

- **优先级**：P1
- **复杂度**：S
- **状态**：Done
- **来源**：设计评审 2026-03-08
- **描述**：因安全原因后端不返回 `auth_token`，编辑时 token 字段总是空白。用户可能误以为 token 丢失，或不确定留空是否会清除已有 token。
- **涉及文件**：`frontend/src/components/agent-version/AgentVersionTab.tsx`、`backend/app/services/agent_version_service.py`
- **建议方案**：已配置 token 时显示 placeholder "已配置，留空表示不修改"；后端 update 时 token 为空则跳过更新。

### UX-05 对话气泡缺少轮次编号

- **优先级**：P2
- **复杂度**：S
- **状态**：Done
- **来源**：设计评审 2026-03-08
- **描述**：P5 对话剧场及批测详情页的对话气泡没有轮次编号。12 轮以上的对话很长，难以定位裁判总结中提到的具体轮次。
- **涉及文件**：`frontend/src/components/shared/ConversationBubbles.tsx`
- **建议方案**：每轮对话左侧增加轮次编号（如 "R1"、"R2"），一轮 = 一组 user + assistant 消息。

### UX-07 项目列表空状态

- **优先级**：P2
- **复杂度**：S
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：新用户首屏是空的项目列表，没有引导文案。
- **建议方案**：空状态显示插图 + "创建你的第一个评测项目" + 新建按钮。

### UX-08 无 404 路由

- **优先级**：P3
- **复杂度**：S
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：前端 `App.tsx` 没有 catch-all 路由，访问不存在的路径显示空白 layout。
- **涉及文件**：`frontend/src/App.tsx`
- **建议方案**：添加 `*` 路由，渲染 404 页面或重定向到 `/projects`。

### UX-10 对话剧场布局与交互 bug

- **优先级**：P0
- **复杂度**：M
- **状态**：Done
- **来源**：用户反馈 2026-03-09
- **描述**：P5 对话剧场存在三个布局/交互问题：
  1. **对话区固定 500px 不自适应**：`ConversationBubbles` 使用 `maxHeight={500}` 硬编码，无论视口多高对话区都只有 500px，浪费空间
  2. **实时对话不自动滚动到最新**：`conversationEndRef` 放在 `ConversationBubbles` 的滚动容器外部，`scrollIntoView` 滚动的是页面而非对话容器内部
  3. **右侧裁判区空状态缺失**：当裁判未评价时，40% 的右侧区域仅显示一行小文字，其余完全空白，视觉上像页面 bug
- **涉及文件**：`frontend/src/pages/DialogTheater.tsx`、`frontend/src/components/shared/ConversationBubbles.tsx`
- **建议方案**：
  - 对话区改用 `calc(100vh - offset)` 自适应高度，或 ConversationBubbles 接收外部 ref 控制
  - 将 `conversationEndRef` 移入 ConversationBubbles 的滚动容器内部，或让组件暴露 `scrollToBottom` 方法
  - 右侧裁判区增加空状态骨架（如灰色 Skeleton 卡片 + 阶段文案居中展示）

### UX-09 配置表单信息结构扁平，可读性差

- **优先级**：P1
- **复杂度**：M
- **状态**：Done
- **来源**：用户反馈 2026-03-09
- **描述**：三处配置表单存在信息结构问题：
  1. **Agent 版本 Modal**：12 个字段平铺在 640px 弹窗里，基础信息（名称/描述）、连接配置（endpoint/method/auth）、协议配置（request_template/response_path/end_signal）无视觉分组
  2. **裁判配置 / 模型配置**：始终处于编辑态，无查看/编辑模式切换。配置项多时 P3 页面超长，用户难以快速浏览当前配置
- **涉及文件**：`frontend/src/components/agent-version/AgentVersionTab.tsx`、`frontend/src/components/judge-config/JudgeConfigTab.tsx`、`frontend/src/components/model-config/ModelConfigTab.tsx`
- **建议方案**：
  - Agent 版本 Modal：用 Divider 或 Typography.Title 将字段分为「基础信息」「连接配置」「协议配置」三组
  - 裁判配置 / 模型配置：增加查看态（Typography/Descriptions 紧凑展示）和编辑态（Form 表单）的切换，默认查看态

---

## AR · 架构

### AR-01 API 层架构不一致（部分路由缺 Service 层）

- **优先级**：P1
- **复杂度**：M
- **状态**：Done
- **来源**：设计评审 2026-03-08
- **描述**：`projects` 和 `agent_versions` 已抽取 service 层，但 `test_cases`（create/update/delete）、`model_configs`、`providers` 的 CRUD 逻辑仍直接写在路由函数中，违反架构约定。
- **涉及文件**：`backend/app/api/test_cases.py`、`backend/app/api/model_configs.py`、`backend/app/api/providers.py`
- **建议方案**：为这三个资源分别创建 service 文件，路由层仅做参数解析和响应构造。

### AR-02 异常处理不统一

- **优先级**：P1
- **复杂度**：M
- **状态**：Done
- **来源**：设计评审 2026-03-08
- **描述**：`test_cases.py`、`judge_configs.py`、`model_configs.py`、`providers.py` 仍直接 raise `HTTPException`，与 `main.py` 注册的领域异常处理器（`NotFoundError` → 404）模式不一致。
- **涉及文件**：同 AR-01 涉及文件 + `backend/app/api/judge_configs.py`
- **建议方案**：统一改为 raise 领域异常，由 main.py 的全局处理器转换为 HTTP 响应。与 AR-01 一起修复。

### AR-03 `ConflictError` 已注册但从未使用

- **优先级**：P2
- **复杂度**：S
- **状态**：Done
- **来源**：设计评审 2026-03-08
- **描述**：`exceptions.py` 定义了 `ConflictError`，`main.py` 注册了 409 处理器，但代码中没有任何地方 raise 它。
- **涉及文件**：`backend/app/exceptions.py`、`backend/app/main.py`
- **建议方案**：在 provider 重名、项目重名等场景使用它；或确认不需要则移除。
- **解决**：P1-2 中 provider_service 使用 ConflictError 处理供应商重名。

---

## DM · 数据模型

### DM-02 JudgeConfig 整体替换策略浪费 UUID

- **优先级**：P2
- **复杂度**：M
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：`judge_config_service.save_judge_config` 每次保存时删除所有 `checklist_items` 和 `eval_dimensions` 后重建。Schema 中 `ChecklistItemData.id` 声明了可选 UUID 但从未使用。频繁编辑产生大量废弃记录（虽然已级联删除，但 UUID 不可回收）。
- **涉及文件**：`backend/app/services/judge_config_service.py`、`backend/app/schemas/judge_config.py`
- **建议方案**：MVP 阶段影响不大，可保持现状。后续改为 diff 更新（有 id 则更新，无 id 则创建，多余的删除）。

---

## SE · 安全

### SE-01 敏感数据明文存储

- **优先级**：P1
- **复杂度**：M
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：`agent_versions.auth_token` 和 `provider_configs.api_key` 在数据库中明文存储。MVP 本地使用可接受，但上线前必须加密。
- **涉及文件**：`backend/app/models/agent_version.py`、`backend/app/models/provider_config.py`
- **建议方案**：使用对称加密（如 Fernet），密钥通过环境变量注入。写入时加密，读取时解密，API 层保持现有 `auth_token_set: bool` 模式不变。

---

## EN · 工程质量

### EN-01 `datetime.utcnow()` 已弃用

- **优先级**：P2
- **复杂度**：S
- **状态**：Done
- **来源**：设计评审 2026-03-08
- **描述**：`batch_scheduler.py` 使用 `datetime.utcnow()`，该方法在 Python 3.12+ 已弃用。
- **涉及文件**：`backend/app/services/batch_scheduler.py`
- **建议方案**：替换为 `datetime.now(timezone.utc).replace(tzinfo=None)`（因 asyncpg 不接受 timezone-aware datetime 写入 `timestamp without time zone` 列）。

### EN-02 `LLMAdapter.chat_json()` 的 `json_schema` 参数无用

- **优先级**：P2
- **复杂度**：S
- **状态**：Done
- **来源**：设计评审 2026-03-08
- **描述**：`base.py` 抽象方法声明了 `json_schema` 参数，但 `OpenAIAdapter` 和 `AnthropicAdapter` 都未使用它。
- **涉及文件**：`backend/app/llm/base.py`、`backend/app/llm/openai_adapter.py`、`backend/app/llm/anthropic_adapter.py`
- **建议方案**：移除该参数（当前无调用方传入），或在 OpenAI 适配器中实现 structured outputs 支持。

### EN-04 批测/用例 "running" 状态无超时恢复机制

- **优先级**：P0
- **复杂度**：M
- **状态**：Done
- **来源**：用户反馈 2026-03-09
- **描述**：批测执行中如果服务进程崩溃/重启，或请求链路中断（如 Agent API 无响应后重启服务），`batch_tests.status` 和 `test_results.status` 会永远停留在 `running`，无法自动恢复。具体缺陷：
  1. **无 stale recovery**：`main.py` 没有 lifespan handler，启动时不检查/清理遗留的 running 记录
  2. **无单用例整体超时**：虽然单次 HTTP 请求有超时（JSON 60s / SSE 300s），但 20 轮对话总耗时无上限
  3. **无批测级超时**：整个批测没有最大执行时长限制
- **涉及文件**：`backend/app/main.py`、`backend/app/services/batch_scheduler.py`
- **建议方案**：
  - 在 FastAPI lifespan 中添加启动清理：将所有 `running` 状态的 batch 标记为 `failed`，running 的 test_result 标记为 `failed`（error_message: "服务重启，执行中断"）
  - `_run_single_test` 外层包裹 `asyncio.wait_for(timeout=600)`（单用例 10 分钟上限）
  - 可选：batch 级别超时

### EN-03 前端 `pass_threshold` 类型不匹配

- **优先级**：P2
- **复杂度**：S
- **状态**：Done
- **来源**：设计评审 2026-03-08
- **描述**：后端 Pydantic 的 `Numeric` 类型序列化为字符串，前端 TypeScript 类型标注为 `number`，组件中用 `Number(config.pass_threshold)` 显式转换。类型声明与运行时行为不一致。
- **涉及文件**：`frontend/src/types/judgeConfig.ts`、`frontend/src/components/judge-config/JudgeConfigTab.tsx`
- **建议方案**：后端 schema 中对 `pass_threshold` 使用 `float` 类型（或添加 validator 转为 float），确保 JSON 序列化为数字而非字符串。

---

## PF · 性能

（暂无条目）

---

## FT · 新功能

### FT-01 批测记录删除功能

- **优先级**：P1
- **复杂度**：M
- **状态**：Done
- **来源**：设计评审 2026-03-08，用户反馈 2026-03-09（提升优先级）
- **描述**：批测 API 没有 DELETE 端点。调试阶段会产生大量无效批测记录，无法清理，列表越来越长，干扰有效数据查阅。
- **涉及文件**：`backend/app/api/batch_tests.py`、`frontend/src/pages/ProjectWorkbench.tsx`
- **建议方案**：后端增加 `DELETE /api/projects/:id/batch-tests/:bid`，级联删除关联的 `test_results`，运行中的批测不可删除。前端列表增加删除按钮（Popconfirm 二次确认）。

### FT-02 裁判一致性验证机制

- **优先级**：P2
- **复杂度**：L
- **状态**：Open
- **来源**：设计评审 2026-03-08
- **描述**：Anthropic 适配器无原生 JSON mode，裁判输出稳定性依赖 prompt 工程。建议 MVP 验证阶段收集裁判一致性数据，以量化 H1 假设的可信度。
- **建议方案**：提供"重新评判"功能，对同一段对话再次调用裁判，对比两次结果的一致性。或在批测时自动对随机 N% 的用例做双重评判。

### FT-03 批测发起支持选取部分用例

- **优先级**：P2
- **复杂度**：M
- **状态**：Done
- **来源**：用户反馈 2026-03-09
- **描述**：发起批测的确认弹窗只能选 Agent 版本和并发数，测试用例全量跑，无法选取部分用例。调试某个失败场景时只想跑 1-2 个用例，但必须等全量跑完。
- **涉及文件**：`frontend/src/components/batch-test/CreateBatchModal.tsx`、`backend/app/api/batch_tests.py`、`backend/app/schemas/batch_test.py`、`backend/app/services/batch_scheduler.py`
- **建议方案**：Modal 增加用例多选（Checkbox 列表，默认全选），后端 `BatchTestCreate` 增加可选 `test_case_ids: list[UUID] | None` 字段，为 None 时全量，有值时按指定用例跑。

### FT-04 模型管理连通性测试 + Agent 版本弹窗内测试

- **优先级**：P2
- **复杂度**：M
- **状态**：Open
- **来源**：用户反馈 2026-03-09
- **描述**：两个连通性测试体验问题：
  1. **模型管理（ProviderSettings）无连通性测试**：配置完 Provider 的 API Key 后无法验证是否有效，要到批测失败才发现
  2. **Agent 版本连通性测试位置不合理**：测试按钮只在列表页表格行操作里，用户必须先保存关弹窗 → 回列表 → 找到行 → 点测试，流程断裂
- **涉及文件**：`frontend/src/pages/ProviderSettings.tsx`、`frontend/src/components/agent-version/AgentVersionTab.tsx`、`backend/app/api/providers.py`
- **建议方案**：
  - Provider 卡片增加"测试连接"按钮，后端新增 `POST /api/providers/{id}/test`（发送简单 prompt 验证 API key 有效性）
  - Agent 版本 Modal 底部增加"测试连接"按钮（在"确定"旁边），使用表单当前值（非已保存值）调用临时测试接口

---

## 归档（已完成）

> 已修复的问题移到此处，保留记录。格式：`ID | 标题 | 完成日期 | 解决方式`

| ID | 标题 | 完成日期 | 解决方式 |
|----|------|---------|---------|
| DM-01 | 批测不保存裁判配置快照 | 2026-03-08 | v0.2 Phase 1：新增 `config_snapshot` JSONB + `sparring_prompt_snapshot` + `judge_prompt_snapshot` |
| UX-02 | 新项目无步骤引导 | 2026-03-08 | v0.2 Phase 2-3：就绪 API + P2 ReadinessCard 四张卡片（含就绪状态 + 点击跳转） |
| UX-03 | 批测前置校验失败时无跳转 | 2026-03-08 | v0.2 Phase 3：ReadinessCard 点击直接跳转 P3 对应锚点，未就绪时发起按钮禁用并 tooltip 提示 |
| UX-06 | 裁判总结需滚过整段对话 | 2026-03-08 | v0.2 Phase 5：P5 对话剧场左右双栏布局，评判区（Checklist + 评分 + 总结）独立在右侧 40% 区域 |
| FT-01 | 批测记录删除功能 | 2026-03-09 | v0.3 P1-1：DELETE API + Popconfirm 删除按钮，passive_deletes=True |
| AR-01 | API 层架构不一致 | 2026-03-09 | v0.3 P1-2：test_cases/model_configs/providers 抽取 service 层 |
| AR-02 | 异常处理不统一 | 2026-03-09 | v0.3 P1-2：路由层统一委托 service，使用 NotFoundError/ConflictError |
| AR-03 | ConflictError 未使用 | 2026-03-09 | v0.3 P1-2：provider_service 使用 ConflictError 处理供应商重名 |
| UX-04 | Token 字段编辑体验 | 2026-03-09 | v0.3 P1-3：placeholder 提示 + 空值跳过更新 |
| UX-05 | 对话气泡轮次编号 | 2026-03-09 | v0.3 P1-4：每轮显示 R1、R2 居中标记 |
| EN-01 | datetime.utcnow() 弃用 | 2026-03-09 | v0.3 P1-5：替换为 datetime.now(timezone.utc) |
| FT-03 | 批测选取部分用例 | 2026-03-09 | v0.3 P2-1：Checkbox 多选 + test_case_ids 后端过滤 + config_snapshot 联动 |
| UX-09 | 配置表单信息结构扁平 | 2026-03-09 | v0.3 P2-2：Agent Modal Divider 分组 + 裁判/模型查看态/编辑态切换 |
| EN-03 | pass_threshold 类型不匹配 | 2026-03-09 | v0.3 P2-3：schema Decimal→float，全链路统一 |
| EN-02 | chat_json json_schema 无用 | 2026-03-09 | v0.3 P2-4：移除 base/openai/anthropic/mock 四处参数 |
