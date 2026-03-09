# 评测平台 — 开发进度

## v0.3 稳定性与体验修复（进行中）

> 修复 P0 级 bug + 核心体验问题。需求来源：`docs/backlog.md`

---

### Phase BugFix：P0 修复（3 项）

- [x] **BF-1：批测 running 状态恢复机制** `EN-04`
  - FastAPI lifespan 启动清理：将遗留的 `running` batch → `failed`，`running` test_result → `failed`
  - `_run_single_test` 外层包裹 `asyncio.wait_for(timeout=600)`（单用例 10 分钟上限）
  - `_save_failed_result` 增加终态防护，避免超时与内部异常双重计数
- [x] **BF-2：对话剧场布局与交互修复** `UX-10`
  - 对话区改为视口自适应高度（`calc(100vh - 320px)` 替代 `maxHeight=500`）
  - ConversationBubbles 内置自动滚动（useRef + useEffect，不再依赖外部 ref）
  - 右侧裁判区增加空状态占位（Skeleton 卡片 + 阶段文案，排除 completed 状态）
- [x] **BF-3：模型配置页无 Provider 引导** `UX-01`
  - 模型下拉为空时显示 Alert + 跳转"模型管理"链接（加载中不闪烁）

**验证**：重启后无残留 running 记录 → 剧场对话自适应+自动滚动 → 新用户可发现模型配置入口

---

### Phase P1：功能补全 + 架构清理（5 项）✅

- [x] **P1-1：批测记录删除功能** `FT-01`
  - 后端 `DELETE /api/projects/:id/batch-tests/:bid`，级联删除 test_results，running 状态不可删
  - 前端批测列表增加删除按钮（Popconfirm 二次确认）
  - 模型层增加 `passive_deletes=True` 避免 `lazy="raise"` 冲突
- [x] **P1-2：Service 层补全 + 异常处理统一** `AR-01` `AR-02` `AR-03`
  - test_cases / model_configs / providers 抽取 service 层
  - 全部路由改为 raise 领域异常（NotFoundError / ConflictError），移除直接 HTTPException
  - ConflictError 用于 provider 重名检测
- [x] **P1-3：Agent 版本 Token 字段体验** `UX-04`
  - 已配置 token 时 placeholder "已配置，留空表示不修改"
  - 后端 update 时 token 为空则跳过更新
- [x] **P1-4：对话气泡轮次编号** `UX-05`
  - ConversationBubbles 每轮对话增加居中的 "R1"、"R2" 编号（一轮 = user + assistant）
- [x] **P1-5：datetime.utcnow() 替换** `EN-01`
  - batch_scheduler.py 中 `datetime.utcnow()` → `datetime.now(timezone.utc).replace(tzinfo=None)`

**验证**：批测可删除 → 路由层无直接 DB 操作和 HTTPException → Token 编辑体验 → 对话有轮次标记

---

### Phase P2：体验打磨 + 工程清理（4 项）

- [ ] **P2-1：批测选取部分用例** `FT-03`
  - Modal 增加用例多选（Checkbox，默认全选）
  - 后端 BatchTestCreate 增加可选 `test_case_ids` 字段
- [ ] **P2-2：配置表单分组** `UX-09`
  - Agent 版本 Modal 用 Divider 分为「基础信息」「连接配置」「协议配置」三组
  - 裁判配置 / 模型配置增加查看态 / 编辑态切换
- [ ] **P2-3：pass_threshold 类型修复** `EN-03`
  - 后端 schema pass_threshold 改为 float，消除前端 Number() 强转
- [ ] **P2-4：chat_json json_schema 参数清理** `EN-02`
  - 移除 LLMAdapter.chat_json() 的无用 json_schema 参数

**验证**：批测可选用例 → 表单分组清晰 → 类型一致 → 无废代码

---

## 交接备注

**Session #19 (2026-03-09)**：Phase P1 全部完成（5/5）。

- P1-1：批测删除 API + Popconfirm 前端按钮 + passive_deletes 修复
- P1-2：test_cases/model_configs/providers 三组 service 层抽取，路由层清除 HTTPException，ConflictError 用于 provider 重名
- P1-3：Token 编辑 placeholder + 后端空值跳过
- P1-4：ConversationBubbles 居中轮次编号 R1/R2
- P1-5：3 处 datetime.utcnow() → datetime.now(timezone.utc)
- backlog 7 条标记 Done 并归档，P2 移除已完成的 P2-5（AR-03），剩余 4 项
- 下一步：Phase P2（4 项）

**Session #18 (2026-03-09)**：Phase BugFix 全部完成。

- BF-1：lifespan 启动清理 + 单用例超时 + 终态防护（防重复计数）
- BF-2：ConversationBubbles 内置自动滚动 + height prop + 裁判区空状态骨架
- BF-3：ModelConfigTab 无 Provider 时 Alert 引导（含加载态防闪烁）
- 代码审查修复：lifespan 逻辑下沉 service 层、超时保存异常捕获、Skeleton 排除 completed 状态
- v0.3 Phase BugFix 3 个 P0 全部完成，待更新 backlog 状态

**Session #17 (2026-03-09)**：需求管理流程建立 + v0.3 排期。

- 建立 backlog ↔ progress 联动流程（CLAUDE.md 记录）
- backlog 新增 Scheduled 状态，补充复杂度字段（S/M/L）
- 新增 5 条 backlog 条目：UX-09（表单结构）、UX-10（剧场布局）、EN-04（running 卡死）、FT-03（用例选取）、FT-04（连通性测试）
- FT-01 优先级 P2→P1 提升
- 全部 15 条存量 Open 条目经代码验证仍存在
- v0.3 Phase BugFix 排期：EN-04 + UX-10 + UX-01（3 个 P0）

---

<details>
<summary>v0.2 架构重构（已完成） — Phase 1-5 + UX 修复，Session #9-#16</summary>

> 基于 `docs/eval-platform-mvp-spec-v2.md`，将 Tab 式工作台升级为页面下钻式架构。
> 核心变化：P2 配置摘要+批测列表、新增 P3 配置页、P4 表格化、新增 P5 对话剧场、后端快照字段。

- **Phase 1**：DB + Prompt 快照（6 任务 ✅）— Alembic 迁移、config_snapshot JSONB、prompt 快照
- **Phase 2**：就绪状态 API（2 任务 ✅）— ConfigReadiness schema + GET /readiness + 前端 hook
- **Phase 3**：前端路由重构 + P2 + P3（6 任务 ✅）— 去 Tab、ReadinessCard、ProjectConfig 锚点、CreateBatchModal
- **Phase 4**：P4 用例概览改造（2 任务 ✅）— Table 替代 Collapse、排序、进入剧场按钮
- **Phase 5**：P5 对话剧场 + 实时对话写入（6 任务 ✅）— 后端 run_iter 逐轮写入、双栏布局、用例切换、评判区
- **Phase UX**：易用性修复（7 任务 ✅）— 面包屑、readiness 缓存同步、dirty 离开警告、配置预览、状态筛选、头像、用例栏优化
- **端到端验收**：6 项全部通过

**Session #16**：Phase UX 完成。**Session #15**：端到端验收 + dashscope adapter。**Session #14**：Phase 5 完成。**Session #13**：Phase 4 完成。**Session #12**：Phase 3 完成。**Session #11**：Phase 2 完成。**Session #10**：Phase 1 完成。**Session #9**：v2 规划（5 Phase、20 任务）。

</details>

<details>
<summary>v0.1 MVP（已完成） — Phase A-F，Session #1-#8</summary>

> 从零搭建对话 Agent 评测平台 MVP。

- **Phase A**：项目脚手架 + 基础设施（后端 FastAPI + 前端 Vite + Docker + DB + LLM 适配层 + 模型管理）
- **Phase B**：数据管理（项目/Agent 版本/用例/裁判/模型 CRUD）
- **Phase C**：核心引擎（Agent Client + Sparring Runner + Judge Runner + Batch Scheduler + 批测 API）
- **Phase D**：批测界面（批测中心 + 进度轮询 + 统计 + 结果列表）
- **Phase E**：补全打磨（连接测试 + 前置校验 + 异常处理 + 卡片摘要 + 端到端验证）
- **Phase F**：质量加固（数据正确性 + 安全 + 并发 + 架构对齐 + 工程实践）

**Session #1**：项目启动。**Session #2**：Phase A-D。**Session #3**：代码审查。**Session #4**：E3+E4。**Session #5**：E5+Bug 修复。**Session #6**：SSE 支持。**Session #7**：Phase F。**Session #8**：MVP 对齐。

</details>
