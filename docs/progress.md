# 评测平台 — 开发进度

## v0.2 架构重构（进行中）

> 基于 `docs/eval-platform-mvp-spec-v2.md`，将 Tab 式工作台升级为页面下钻式架构。
> 核心变化：P2 配置摘要+批测列表、新增 P3 配置页、P4 表格化、新增 P5 对话剧场、后端快照字段。

### 依赖关系

```
Phase 1 (DB + 快照) ──┬──> Phase 3 (路由 + P2 + P3)
                       │         │
Phase 2 (就绪 API) ───┘         ├──> Phase 4 (P4 改造)
                                │         │
                                └─────────┴──> Phase 5 (P5 剧场)
```

---

### Phase 1：数据库 + Prompt 快照

- [x] **1.1：Alembic 迁移 — 新增 3 个字段**
  - `batch_tests` + `config_snapshot` (JSONB)
  - `test_results` + `sparring_prompt_snapshot` (Text) + `judge_prompt_snapshot` (Text)
- [x] **1.2：更新 SQLAlchemy 模型** — `models/batch_test.py`
- [x] **1.3：更新 Pydantic Schema** — `schemas/batch_test.py`
- [x] **1.4：批测创建时冻结 config_snapshot** — `services/batch_test_service.py`
- [x] **1.5：暴露 Prompt 文本** — `sparring_runner.py` 存 `self.persona_prompt`、`judge_runner.py` 存 `self.last_prompt`
- [x] **1.6：Batch Scheduler 保存快照** — `batch_scheduler.py` 写入两个 prompt 快照

**验证**：迁移成功 → 创建批测有 config_snapshot → 完成后有 prompt 快照 → 现有测试不回归

---

### Phase 2：就绪状态 API

- [x] **2.1：后端就绪接口**
  - `schemas/project.py` 新增 `ConfigReadiness` schema
  - `services/project_service.py` 新增 `get_config_readiness()`
  - `api/projects.py` 新增 `GET /api/projects/{id}/readiness`
- [x] **2.2：前端对接** — `types/project.ts` + `api/projects.ts` + `hooks/useProjects.ts`

**验证**：各配置状态下 `/readiness` 返回正确就绪值

---

### Phase 3：前端路由重构 + P2 + P3

- [x] **3.1：更新路由** — `App.tsx` 新增 `/projects/:id/config`，lazy load ProjectConfig
- [x] **3.2：重写 P2 — ProjectWorkbench** — 去掉 Tabs，改为配置摘要栏 + 批测列表 + `[发起批测]` 按钮
- [x] **3.3：提取 CreateBatchModal** — 从 `BatchTestTab.tsx` 提取为独立组件，新增 `onCreated` 回调
- [x] **3.4：新建 P3 — ProjectConfig** — 4 个 Card 区块 + 锚点滚动，复用现有 Tab 组件
- [x] **3.5：更新前端类型** — `batchTest.ts` 增加 `config_snapshot`、`sparring_prompt_snapshot`、`judge_prompt_snapshot`
- [x] **3.6：清理废弃代码** — 删除 `ExperimentTab.tsx` + `BatchTestTab.tsx`

**验证**：P2 无 Tab + 摘要卡片可点 → P3 四区块正常 → 发起批测跳转 P4 → 导航正常

---

### Phase 4：P4 用例概览改造

- [x] **4.1：提取 ConversationBubbles** — 从 `BatchTestDetail.tsx` 提取为 `components/shared/ConversationBubbles.tsx`
- [x] **4.2：改写 BatchTestDetail → 表格化** — `Table` 替代 `Collapse`，列：用例名/结果/轮次/终止原因/操作
  - 排序：未通过优先(默认) / 按用例序号 / 按轮次
  - `[进入剧场]` 按钮 → P5
  - 运行中状态：进行中 `⏳`，等待中 `⏸`

**验证**：表格正常 → 排序正常 → 进入剧场跳转正确 → 运行中实时更新

---

### Phase 5：P5 对话剧场 + 实时对话写入

**设计决策**：后端改为逐轮写入对话数据，前端轮询即可实现实时观测，无需 WebSocket/SSE。

**后端改动（~40 行）：**
- `SparringRunner.run()` → 改为 async generator `run_iter()`，每轮 yield `(conversation, termination_reason, actual_rounds)`
- `_run_single_test` 中每轮迭代后更新 DB 的 `test_result.conversation` 字段
- 保留原 `run()` 方法作为兼容封装（调用 `run_iter` 消费到底）

**前端改动：**
- `useBatchTestDetail` 已有 3 秒轮询，自动获取最新 conversation 数据
- `ConversationBubbles` 渲染数组，不区分回放/实时，零改动

**任务清单：**

- [x] **5.1：后端逐轮写入** — `SparringRunner` 改为 async generator `run_iter()` + `_run_single_test` 每轮更新 conversation
- [x] **5.2：DialogTheater 页面主体** — 左右双栏布局（60/40），复用 `useBatchTestDetail` 获取数据
- [x] **5.3：顶部用例切换栏** — 水平标签，按状态着色（✅/❌/⚠️），点击切换 URL，未通过排前
- [x] **5.4：左侧对话区** — ConversationBubbles + 终止原因标注 + 幕后信息折叠（角色卡 + 对练 Prompt）
- [x] **5.5：右侧评判区** — Checklist 结果 + Evaluation 评分 + 裁判总结 + 裁判 Prompt 折叠
- [x] **5.6：运行中状态** — 轮询刷新，对话实时追加，评判区状态文案（⏳ 对话进行中 / 🔄 裁判评判中）

**验证**：P4 进入剧场 → P5 双栏正确 → 用例切换正常 → 幕后信息有内容 → 运行中实时追加对话 → 返回正常

---

### Phase UX：易用性修复

- [x] **U7：全局面包屑导航** — P2/P3/P4/P5 用 BreadcrumbNav 替代 ← 返回按钮，支持跨级跳转
- [x] **U2：配置保存后同步就绪状态缓存** — 4 个配置 hook 的 onSuccess 增加 invalidate readiness
- [x] **U1：P3 离开未保存警告** — JudgeConfigTab/ModelConfigTab 追踪 dirty 状态，useBlocker + beforeunload 拦截
- [x] **U3：发起批测 Modal 增加配置预览** — 展示 Checklist 条目 Tag 和评判维度名称
- [x] **U5：P4 状态筛选** — 结果列增加 Ant Design Table column filters（通过/未通过/失败/进行中/等待中）
- [x] **U6：对话气泡角色头像** — Avatar + UserOutlined/RobotOutlined 替代 Tag
- [x] **U4：P5 用例切换栏优化** — 水平滚动替代 flexWrap + 状态筛选下拉 + 进度统计

---

### 端到端验收 ✅

完成所有 Phase 后：
1. ✅ 创建项目 → P2 四张卡片全未就绪，发起按钮灰色
2. ✅ 点卡片 → P3 锚点定位，配置完成后返回 P2 全绿
3. ✅ 发起批测 → 自动跳转 P4，实时进度（⏳ 进行中 / ⏸ 等待中）
4. ✅ 进入剧场 → P5 双栏，切换用例，对话实时追加，Checklist/Evaluation/裁判总结
5. ✅ 全部 `← 返回` 正常（P5→P4→P2→P1）
6. ✅ 路由守卫 — 无效批测 ID 显示"批测不存在"

---

## 交接备注

**Session #16 (2026-03-09)**：Phase UX 易用性修复完成（7 项）。

- 基于设计评审（Value → Ease of Use → Delight 框架）识别的 7 个易用性问题全部修复
- 新增 BreadcrumbNav 共享组件，P2-P5 四个页面均用面包屑替代返回按钮
- 配置保存后自动 invalidate readiness 缓存（4 个 hooks），P3→P2 就绪状态实时同步
- 裁判/模型配置增加 dirty state tracking + useBlocker 离开确认 + beforeunload
- 发起批测 Modal 展示 Checklist 条目和评判维度名称
- P4 结果表格增加状态筛选（column filters）
- 对话气泡用 Avatar 替代 Tag 增强角色可区分性
- P5 用例切换栏改为水平滚动 + 状态筛选 + 进度统计
- 代码审查修复：blocker.state 依赖、dataLoaded 重置、类型导入路径
- TypeScript 无报错

**Session #15 (2026-03-08)**：端到端验收完成 + dashscope adapter。

- 端到端验收 6 项全部通过（P2 就绪卡片、P3 锚点、P4 表格化 + 实时进度、P5 剧场双栏 + 用例切换 + 评判区、返回导航、路由守卫）
- 使用真实 DashScope API（qwen3-coder-plus）+ Mock Agent 完成完整批测流程
- 新增 `dashscope` LLM adapter 映射（复用 OpenAI adapter，支持阿里百炼平台）
- 24 个后端测试通过，TypeScript 无报错
- v0.2 架构重构全部完成（Phase 1-5 + 端到端验收）

**Session #14 (2026-03-08)**：Phase 5 完成。

- 6 个任务全部完成：后端逐轮写入 + DialogTheater 完整实现（双栏布局、用例切换、对话区、评判区、运行中状态）
- 后端：SparringRunner 新增 `run_iter()` async generator，每轮 yield；`_run_single_test` 每轮写入 conversation 到 DB（带 try/except 容错）
- 前端：DialogTheater 页面 — 左 60% 对话区（ConversationBubbles + 终止原因 + 幕后信息折叠）、右 40% 评判区（Checklist + Evaluation + 裁判总结 + 裁判 Prompt 折叠）
- 顶部用例切换栏：按状态着色，未通过排前，点击切换 URL
- 运行中状态：已有 3 秒轮询自动获取最新数据，对话实时追加 + auto-scroll，评判区显示阶段文案
- 代码审查修复：删除未使用变量、⭐ repeat 边界保护、逐轮写入 try/except 容错
- 24 个后端测试通过，TypeScript 无报错

下一步：端到端验收。所有 Phase (1-5) 已完成。

**Session #13 (2026-03-08)**：Phase 4 完成。

- 2 个任务全部完成：ConversationBubbles 提取 + BatchTestDetail 表格化改造
- P4 改造：Collapse 展开式 → Table 表格化，列：用例名/结果/轮次/终止原因/操作
- 排序：未通过优先（默认）/ 按用例序号 / 按轮次
- 运行中状态：⏳ 进行中 / ⏸ 等待中
- [进入剧场] 按钮预连 P5 路由（DialogTheater 占位页）
- 代码审查修复：DialogTheater 路由守卫、通过率分母语义修正、key 优化、BatchTestDetail lazy 加载
- 文档同步：architecture.md 路由表更新、conventions.md 补充 shared/ 目录说明
- 24 个后端测试通过，TypeScript 无报错

下一步：Phase 5（P5 对话剧场）。

**Session #12 (2026-03-08)**：Phase 3 完成。

- 6 个任务全部完成：路由重构、P2 重写、CreateBatchModal 提取、P3 新建、类型更新、废弃代码清理
- P2 改造：去掉 4-Tab 工作台，改为配置摘要栏（4 个 ReadinessCard + 就绪状态）+ 批测记录列表
- P3 新建：ProjectConfig 页面，4 个 Card 纵向排列 + URL 锚点滚动定位
- CreateBatchModal：独立组件，支持 `onCreated` 回调（创建后自动跳转 P4）
- 代码审查修复：Modal 条件渲染改为始终渲染、catch 块拆分校验与 API 错误、filter 类型安全
- 24 个后端测试通过，TypeScript 无报错

下一步：Phase 4（P4 用例概览改造）。

**Session #11 (2026-03-08)**：Phase 2 完成。

- 2 个任务全部完成：后端就绪接口 + 前端对接
- 后端：`ConfigReadiness` schema、`get_config_readiness()` service（4 项检查：Agent 版本连接、测试用例、裁判配置、模型配置）、`GET /readiness` API
- 前端：`ConfigReadiness` 类型、`getReadiness` API 方法、`useProjectReadiness` hook
- 24 个测试通过，TypeScript 无报错，代码审查通过

下一步：Phase 3（前端路由重构 + P2 + P3）。

**Session #10 (2026-03-08)**：Phase 1 完成。

- 6 个任务全部完成：Alembic 迁移、模型/Schema 更新、config_snapshot 冻结、prompt 暴露、快照持久化
- 代码审查修复：将 persona_prompt 构建提取为 `_build_persona_prompt()`，在 `__init__` 中调用，避免第一轮即结束时快照为 None
- 24 个测试全部通过，迁移已应用到数据库

下一步：Phase 2（就绪状态 API）。

**Session #9 (2026-03-08)**：v2 迭代规划。

对比 `eval-platform-mvp-spec-v2.md` 与现有实现，完成完整评估：
- 拆分为 5 个 Phase、20 个任务，按依赖关系排序
- 工作量分布：~70% 前端、~20% 后端、~10% 数据库

---
---

## v0.1 MVP（已完成）

> 从零搭建对话 Agent 评测平台 MVP。Phase A-F 全部完成，含质量加固。

<details>
<summary>Phase A-F 任务清单（全部 ✅）</summary>

### Phase A：项目脚手架 + 基础设施
- [x] A1：初始化后端项目
- [x] A2：初始化前端项目
- [x] A3：Docker Compose
- [x] A4：数据库模型 + 迁移
- [x] A5：LLM 适配层
- [x] A6：全局模型管理 API
- [x] A7：全局模型管理前端页面

### Phase B：数据管理
- [x] B1-B10：项目/Agent版本/用例/裁判/模型 CRUD API + 前端页面

### Phase C：核心引擎
- [x] C1：Agent Client（HTTP 调用、模板替换、JSONPath 解析）
- [x] C2：Sparring Runner（对练循环、三种终止条件、[END] 标记）
- [x] C3：Judge Runner（Prompt 组装、JSON 输出、通过判定）
- [x] C4：Batch Scheduler（asyncio.Semaphore 并发、进度追踪）
- [x] C5：批测 API（创建/列表/详情/进度、后台任务启动）

### Phase D：批测界面
- [x] D1-D5：批测中心 + 进度轮询 + 统计摘要 + 用例结果列表 + 展开区

### Phase E：补全 + 打磨
- [x] E1-E5：连接测试 + 前置校验 + 异常处理 + 卡片摘要 + 端到端验证

### Phase F：质量加固
- [x] F1-F5：数据正确性 + 安全加固 + 并发稳定性 + 架构对齐 + 工程实践

</details>

<details>
<summary>Session #1-#8 交接备注</summary>

**Session #1**：项目启动。产品需求分析、技术架构设计、文档体系搭建。

**Session #2**：完成 Phase A-D。后端 FastAPI 骨架、10 张表、LLM 适配层、全部 CRUD API、核心引擎。前端 Vite+React+TS+AntD、全部页面。

**Session #3**：代码质量审查 + 7 步修复（安全漏洞、数据正确性、架构违规等 20 个问题）。

**Session #4**：E3 异常处理 + E4 卡片摘要。

**Session #5**：E5 端到端验证 + 6 个 Bug 修复。

**Session #6**：SSE 流式响应支持 + 前端白屏修复。

**Session #7**：Phase F 质量加固（12 严重问题 + 15 改进建议全部修复）。

**Session #8**：MVP 需求对齐（9 项偏差修正）。

</details>
