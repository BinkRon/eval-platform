# 评测平台 — 开发进度

## v0.1 MVP（进行中）

> 从零搭建对话 Agent 评测平台 MVP。核心验证：自动化对练 + 裁判能可靠发现 Agent 的真实问题。

### Phase A：项目脚手架 + 基础设施

- [x] **A1：初始化后端项目** ✅
- [x] **A2：初始化前端项目** ✅
- [x] **A3：Docker Compose** ✅
- [x] **A4：数据库模型 + 迁移** ✅
- [x] **A5：LLM 适配层** ✅
- [x] **A6：全局模型管理 API** ✅
- [x] **A7：全局模型管理前端页面** ✅

**Phase A 里程碑**：✅ 完成

---

### Phase B：数据管理

- [x] **B1：项目 CRUD API** ✅
- [x] **B2：P1 项目列表页** ✅
- [x] **B3：Agent 版本 CRUD API** ✅
- [x] **B4：P2-T1 Agent 版本管理页** ✅
- [x] **B5：测试用例 CRUD API** ✅
- [x] **B6：P2-T2 用例子 Tab** ✅
- [x] **B7：裁判配置 API** ✅
- [x] **B8：P2-T2 裁判子 Tab** ✅
- [x] **B9：模型配置 API** ✅
- [x] **B10：P2-T3 模型配置页** ✅

**Phase B 里程碑**：✅ 完成

---

### Phase C：核心引擎

- [x] **C1：Agent Client** ✅ — HTTP 调用、模板替换、JSONPath 解析
- [x] **C2：Sparring Runner** ✅ — 对练循环、三种终止条件、[END] 标记
- [x] **C3：Judge Runner** ✅ — Prompt 组装、JSON 输出、通过判定
- [x] **C4：Batch Scheduler** ✅ — asyncio.Semaphore 并发、进度追踪
- [x] **C5：批测 API** ✅ — 创建/列表/详情/进度、后台任务启动

**Phase C 里程碑**：✅ 完成

---

### Phase D：批测界面

- [x] **D1：P2-T4 批测中心** ✅ — 列表 + 发起批测弹窗
- [x] **D2：进度轮询** ✅ — TanStack Query refetchInterval 3s
- [x] **D3：P3 统计摘要** ✅ — Checklist 通过率 + Evaluation 维度均分
- [x] **D4：P3 用例结果列表** ✅ — Collapse 折叠/展开 + 排序切换
- [x] **D5：P3 用例展开区** ✅ — Checklist + Evaluation + 对话气泡 + 裁判总结

**Phase D 里程碑**：✅ 完成

---

### Phase E：补全 + 打磨（进行中）

- [x] **E1：Agent 版本连接测试** ✅ — POST /test 接口 + 前端测试按钮 + 状态更新
- [x] **E2：批测前置校验** ✅ — 校验 Agent 版本/用例/裁判配置/模型配置
- [x] **E3：异常处理完善** ✅ — 分阶段错误处理 + 裁判重试 + 批测状态修复 + 前端失败展示
- [x] **E4：项目卡片摘要信息** ✅ — 聚合查询 + ROW_NUMBER 窗口函数 + 前端卡片摘要渲染
- [x] **E5：端到端验证** ✅ — 完整 API 链路验证 + 6 个 Bug 修复 + 代码审查

**Phase E 里程碑**：✅ 完成 — 非技术人员能独立完成完整评测流程。

---

## 交接备注

**Session #1 (2026-03-06)**：项目启动。完成产品需求分析（三份文档）、技术架构设计、文档体系搭建。确认技术选型。

**Session #2 (2026-03-06)**：完成 Phase A 全部 7 个任务 + Phase B 全部 10 个任务 + Phase C 全部 5 个任务 + Phase D 全部 5 个任务。

后端完成：FastAPI 骨架、10 张表 SQLAlchemy 模型 + Alembic 迁移、LLM 适配层（Anthropic/OpenAI + 工厂）、全部 CRUD API（providers/projects/agent-versions/test-cases/judge-config/model-config/batch-tests）、核心引擎（AgentClient/SparringRunner/JudgeRunner/BatchScheduler）。

前端完成：Vite + React + TS + Ant Design + TanStack Query + React Router、全局模型管理页、项目列表页（卡片 + CRUD 弹窗）、项目工作台（5 个 Tab：Agent 版本/测试用例/裁判配置/模型配置/批测中心）、批测详情页（统计摘要 + Checklist 通过率 + Evaluation 均分 + 用例折叠列表 + 对话气泡 + 裁判总结）。

基础设施：Docker Compose + Dockerfile、本地 PostgreSQL 14 连接。

下一步：Phase E 补全打磨。

**Session #3 (2026-03-06)**：代码质量审查 + 7 步修复。

审查发现 20 个问题（安全漏洞、数据正确性、架构违规、前端缺陷等），按优先级分 7 步完成修复：

1. **P0 安全与数据正确性**：模板注入修复（agent_client.py 改为先解析 JSON 再递归替换占位符）、并发计数竞态修复（batch_scheduler.py 改用 SQL 原子递增）、后台任务 GC 回收（batch_tests.py 持有 task 引用）
2. **P0 类型 + P1 功能**：JSONB 类型对齐（provider_config.py dict→list）、temperature/max_tokens 透传（BatchContext→SparringRunner/JudgeRunner→LLM）、Anthropic 代码块解析修复
3. **P2 架构违规**：提取 batch_test_service.py 和 judge_config_service.py、agent_versions.py 消除裸字典返回、移除冗余 db.refresh() 调用
4. **前端轮询**：useBatchTests 改为条件轮询（refetchInterval 函数式）、消除 N+1 轮询、client.ts 422 错误格式化
5. **前端防御性编程**：useParams 判空、handleSubmit/handleDelete try/catch
6. **配置与健壮性**：debug 默认 False、CORS 配置化、LLM 适配层增加 timeout/max_retries
7. **前端类型目录重构**：新建 src/types/ 目录，7 个模块类型文件 + barrel index.ts，API 文件改为从 types/ 导入并 re-export

**Session #4 (2026-03-06)**：完成 E3 异常处理完善。

修改 4 个文件：
1. **agent_client.py**：捕获 httpx 异常（超时/连接/HTTP 状态码/网络错误），JSON 解析异常包装为明确的 RuntimeError
2. **judge_runner.py**：裁判 JSON 格式错误时重试 1 次（符合 MVP 需求 10.3 节要求）
3. **batch_scheduler.py**：将单个大 try/catch 拆分为对练/裁判两个阶段；裁判失败时保留对话记录；提取 `_save_failed_result` helper；成功路径合并为单事务；全部用例失败时批测状态标记为 "failed"
4. **BatchTestDetail.tsx**：修复 React Hooks 规则违反；失败用例展示错误信息 + 对话记录（评判前）；失败用例 label 不再显示 "未通过" 误导语义；批测状态 Tag 支持中文标签

完成 E4 项目卡片摘要信息：
1. **project.py (schema)**：新增 LatestBatchSummary + 扩展 ProjectResponse（版本数/用例数/批测数/最近批测摘要）
2. **projects.py (API)**：批量 count 子查询 + ROW_NUMBER 窗口函数取每项目最近 2 次批测 + 通过率环比计算
3. **project.ts (types)**：扩展 Project 接口 + LatestBatchSummary 接口
4. **ProjectList.tsx**：卡片显示版本数、最近批测摘要（时间+版本+通过率+变化箭头）、用例数、累计批测

下一步：E5 端到端验证。

**Session #5 (2026-03-06)**：完成 E5 端到端验证。

完整 API 链路走通：创建 Provider → 创建项目 → 创建 Agent 版本 → 创建用例 → 配置裁判 → 配置模型 → 创建批测 → 轮询进度 → 查看详情。

发现并修复 6 个 Bug：
1. **db.refresh 缺失**：`server_default=func.now()` 的时间戳在 commit 后为 None，导致 Pydantic 序列化 500。所有 create/update 端点添加 `await db.refresh(obj)`
2. **时间戳列类型错误**：Alembic 自动生成的迁移将 TimestampMixin 字段映射为 `sa.String()` 而非 `sa.DateTime()`。新建迁移 `bb85f71f2b8a` 将 8 张表的 created_at/updated_at ALTER 为 TIMESTAMP
3. **事务冲突**：`async with db.begin()` 与 asyncpg 自动开始的事务冲突。judge_configs.py、batch_tests.py 改为直接调用 + `await db.commit()`
4. **时区感知 datetime 写入失败**：`datetime.now(UTC)` 返回 timezone-aware datetime，asyncpg 拒绝写入 `timestamp without time zone` 列，导致批测状态卡在 "running"。batch_scheduler.py 改用 `datetime.utcnow()`
5. **dict 转换错误**：`dict(await db.execute(...))` 对 ChunkedIteratorResult 不可用。改为 `dict(result.all())`
6. **307 重定向**：前端不带尾部斜杠，FastAPI 路由用 `"/"` 导致 307 重定向。设置 `redirect_slashes=False` + 所有集合路由改为 `""`

代码审查修复：
- `logging.basicConfig` 移到业务 import 之前
- 全局异常处理器排除 HTTPException，避免覆盖 FastAPI 内置 404/400 处理

架构审查发现 2 个待优化项（记录但不阻塞 MVP）：
- `batch_test_service.py` 的 service 层直接使用 HTTPException（应抛业务异常）
- `projects.py` 的 `list_projects` 路由函数包含过多业务逻辑（应提取到 service 层）

Phase E 全部完成，v0.1 MVP 所有 Phase (A-E) 开发完毕。
