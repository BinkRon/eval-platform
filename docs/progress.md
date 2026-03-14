# 评测平台 — 开发进度

## v1.0 二期功能实现（进行中）

> PRD：[`docs/prd/eval-platform-phase2-spec.md`](prd/eval-platform-phase2-spec.md)
> 核心：构建 Agent（AI 辅助配置）+ 数据模型简化 + Prompt 组装重构
> 验证假设：H3 效率假设（配置时间缩短 50%）、H4 质量假设（AI 生成配置不低于手动）

---

### Phase 1：数据模型迁移

> TestCase / EvalDimension 字段重构 + 新增 ProjectFile / BuilderConversation 实体

- [x] **1-1：Alembic 迁移脚本** `[M]`
  - TestCase：ADD `sparring_prompt` → 数据迁移（拼接 persona_background + persona_behavior）→ NOT NULL → DROP 旧字段
  - TestCase：`first_message` 改 nullable（default “喂？”）、`max_rounds` default 50
  - EvalDimension：ADD `judge_prompt_segment` → 数据迁移（拼接 description + level_*_desc）→ NOT NULL → DROP 旧字段
  - 新表：`project_files`、`builder_conversations`
- [x] **1-2：更新 SQLAlchemy Models** `[S]`
  - `backend/app/models/test_case.py` — 删 persona_*，加 sparring_prompt
  - `backend/app/models/judge_config.py` — EvalDimension 删 description/level_*_desc，加 judge_prompt_segment
  - 新建 `project_file.py`、`builder_conversation.py`
  - `project.py` 加关系 + 级联删除；`__init__.py` 注册新模型
- [x] **1-3：更新 Pydantic Schemas** `[S]`
  - `backend/app/schemas/test_case.py` — 适配新字段，first_message 选填，max_rounds default 50 / max 100
  - `backend/app/schemas/judge_config.py` — EvalDimensionData 适配新字段
- [x] **1-4：更新 TypeScript Types** `[S]`
  - `frontend/src/types/testCase.ts`、`judgeConfig.ts` — 适配新字段
  - 新建 `projectFile.ts`、`builderConversation.ts`
- [x] **1-5：更新测试 Fixtures** `[S]`
  - `backend/tests/conftest.py` — test_case_factory 用 sparring_prompt；eval_dimension_factory 用 judge_prompt_segment
  - 额外适配：sparring_runner / judge_runner / batch_test_service / judge_config_service + 前端 TestCaseTab / JudgeConfigTab

**验证**：`alembic upgrade head` ✓ → `pytest` 通过 ✓ → `tsc --noEmit` 通过 ✓

---

### Phase 2：核心引擎适配

> Prompt 组装使用新字段 + 默认 System Prompt + 旧 snapshot 向后兼容

- [x] **2-1：SparringRunner Prompt 组装** `[S]`（Phase 1 已完成）
  - `sparring_runner.py` — `_build_persona_prompt` 直接注入 sparring_prompt，不再拼 persona_background + persona_behavior
  - `run_iter` — first_message 取 `self.test_case.first_message or “喂？”`
- [x] **2-2：JudgeRunner Prompt 组装 + 旧 snapshot 兼容** `[S]`（Phase 1 已完成）
  - `judge_runner.py` — `_build_prompt` Evaluation 部分用 judge_prompt_segment
  - 向后兼容：`getattr(dim, 'judge_prompt_segment', None)` fallback 旧字段格式
- [x] **2-3：默认 System Prompt 常量** `[S]`
  - 新建 `backend/app/services/prompt_defaults.py` — DEFAULT_SPARRING_SYSTEM_PROMPT + DEFAULT_JUDGE_SYSTEM_PROMPT（PRD §3.4）
  - `batch_scheduler.py` — system_prompt 为空时使用默认值
  - 注意：[END] 标记由 `_build_persona_prompt` 动态追加，默认 prompt 不含以避免重复
- [x] **2-4：judge_config_service 适配** `[S]`（Phase 1 已完成）
  - `judge_config_service.py` — save 时使用 judge_prompt_segment
- [x] **2-5：更新核心测试** `[M]`
  - `test_sparring_runner.py` — 新增 TestPromptBuilding（prompt 注入 + first_message=None 回退）
  - `test_judge_runner.py` — 新增旧 snapshot 兼容 + judge_prompt_segment 优先测试
  - 新建 `test_prompt_defaults.py` — 默认 prompt 非空 + 关键内容 + END 不重复
  - 重构 `conftest.py` MockLLMAdapter — chat_json_responses 原生支持 Exception，消除测试中 monkey-patch

**验证**：`pytest` 全部通过 ✓

---

### Phase 3：P3 前端适配

> 用例编辑弹窗简化 + Eval 维度编辑重构 + 默认 Prompt 展示

- [x] **3-1：TestCaseTab 改造** `[M]`
  - 列表列：名称 + sparring_prompt 截取 40 字 + 操作（Phase 1 已适配）
  - 编辑弹窗：sparring_prompt TextArea 增大（rows=8）+ 高级配置折叠面板（first_message、max_rounds、sort_order）
  - Collapse destroyInactivePanel={false} 防止字段值丢失
- [x] **3-2：JudgeConfigTab Eval 维度改造** `[M]`（Phase 1 已适配）
  - 查看态 DimensionCard：名称 + judge_prompt_segment 前 2 行预览
  - 编辑态：name + judge_prompt_segment TextArea + markdown 提示
- [x] **3-3：ModelConfigTab 默认 Prompt** `[S]`
  - 查看态：System Prompt 为空时显示默认值 +「系统默认」标签 + 降低透明度
  - 编辑态：placeholder 提示"留空将使用系统内置 Prompt"
  - 前端默认 Prompt 常量与后端 prompt_defaults.py 严格对齐
- [x] **3-4：P5 对话剧场幕后信息适配** `[S]`（Phase 1 已适配）
  - sparring_prompt_snapshot 直接展示新 prompt 结构

**验证**：`tsc --noEmit` ✓ → 配置页增删改查正常 ✓ → 批测全链路正常 ✓

---

### Phase 4：新增后端 API

> 项目文件 + 构建对话 + 构建 Agent 聊天接口

- [x] **4-1：项目文件 API** `[M]`
  - 新建 service/api/schema：upload（multipart）/ list / delete
  - `config.py` 已有 `FILE_STORAGE_PATH`（Phase 1 配置）
  - 支持 PDF/DOCX/TXT/MD/XLSX/CSV，上限 20MB + 前置 Content-Length 校验
  - 文件名净化（路径遍历防护）、storage_path 不暴露在 API 响应中
- [x] **4-2：构建对话 API** `[S]`
  - 新建 service/api/schema：get_or_create / append_message / clear
  - BuilderConversationResponse.messages 使用 MessageData 类型约束
- [x] **4-3：构建 Agent 聊天 API** `[M]`
  - 新建 `builder_agent_service.py` — 加载项目上下文 + 文件 + 对话历史 → LLM 调用 → 返回响应
  - 新建 `builder_agent.py` API — `POST .../chat`
  - LLM 调用失败不会留下孤立消息（先调用 LLM，成功后再持久化）
- [x] **4-4：文件内容解析器** `[M]`
  - 新建 `file_parser.py` — PDF(pypdf) / DOCX(python-docx) / TXT/MD / XLSX/CSV(openpyxl)
  - `requirements.in` 新增 aiofiles/pypdf/python-docx/openpyxl/python-multipart
- [x] **4-5：API 路由注册** `[S]`
  - `main.py` 注册 project_files / builder_conversations / builder_agent 路由
- [x] **4-6：后端测试** `[M]`
  - 新建 `test_builder_agent.py` — system prompt 内容 + 上下文加载 + LLM 调用流程
  - 新建 `test_file_parser.py` — TXT/MD/CSV/XLSX 解析 + 不支持类型 + 缺失文件
  - 新建 `test_project_file_service.py` — 扩展名校验 + 大小校验 + 文件名净化

**验证**：`pytest` 73 passed ✓ → 双 Agent 审查通过（修复 6 项）✓

---

### Phase 5：构建 Agent 前端 UI

> 悬浮球 + 对话面板 + 确认卡片 + 文件管理

- [x] **5-1：API 层 + Hooks** `[S]`
  - 新建 `frontend/src/api/` — builderAgent / projectFiles / builderConversation
  - 新建 `frontend/src/hooks/` — useBuilderAgent / useProjectFiles / useBuilderConversation
  - 新建 `frontend/src/types/builderAgent.ts` — BuilderChatRequest / BuilderChatResponse
- [x] **5-2：悬浮球组件** `[S]`
  - `components/builder-agent/FloatingButton.tsx` — 右下角固定定位 + 展开/收起 + projectId 变化自动收起
- [x] **5-3：对话面板** `[L]`
  - `components/builder-agent/ChatPanel.tsx` — 标题栏（📁 + 模型选择 + 清空确认 + 收起）+ 消息流 + 输入区
  - Optimistic update：发送时立即显示用户消息，成功后追加助手消息，失败按 snapshot 长度回滚
  - 后端 chat API 自动持久化消息，前端不单独调 appendMessage
- [x] **5-4：消息气泡** `[S]`
  - `components/builder-agent/MessageBubble.tsx` — 用户右对齐/助手左对齐 + react-markdown + rehype-sanitize（XSS 防护）
- [x] **5-5：确认卡片组件** `[M]`
  - GenerateConfirmCard（生成确认：摘要 + Collapse 展开详情 + 取消/修改/确认）
  - OverwriteConfirmCard（覆盖确认：Radio.Group 追加/替换 + 确认）
  - ClarifyCard（澄清请求：选项按钮 + 跳过）
- [x] **5-6：项目文件管理浮层** `[S]`
  - `components/builder-agent/ProjectFileManager.tsx` — Popover 文件列表 + Upload 上传 + Popconfirm 删除
  - 前端校验：扩展名白名单 + 20MB 大小限制；删除 loading 按 file.id 精确匹配
- [x] **5-7：全局布局集成** `[M]`
  - 新建 `layouts/ProjectLayout.tsx` — 项目级 wrapper（Outlet + FloatingButton）
  - `App.tsx` — 项目路由嵌套在 ProjectLayout 下

**验证**：`tsc --noEmit` ✓ → 双 Agent 审查通过（修复 6 项：optimistic update 冲突、XSS 防护、回滚逻辑、清空确认、删除 loading、类型位置）✓

---

### Phase 6：构建 Agent 智能层

> Skill 定义 + 结构化输出解析 + 配置写入

- [x] **6-1：Skill 定义 + System Prompt** `[M]`
  - `builder_agent_service.py` — 完整 system prompt 含角色定义 + 用例生成 Skill（PRD §4.2）+ 裁判配置生成 Skill（PRD §4.3）
- [x] **6-2：结构化输出解析** `[M]`
  - `builder_agent_service.py` — `<generated_config>` XML 标签提取 + `chat_json` 重试 + 卡片类型检测
  - 失败时自动清除标签残留，防止前端渲染 raw XML
- [x] **6-3：配置写入逻辑** `[S]`
  - `builder_agent_service.py` — apply_generated_config：直接 ORM 写入 + 单次 commit（事务一致性）
  - level 映射：required→must, important→should，未知值安全回退
  - 前端确认卡片 loading 态禁用按钮
- [x] **6-4：集成测试** `[M]`
  - `test_builder_agent.py` — 95 个测试全部通过（prompt / parse / card / chat / apply 全覆盖）

**验证**：`pytest` 95 passed ✓ → `tsc --noEmit` ✓ → 双 Agent 审查通过（修复 5 项）✓

---

### Phase 7：文档 + Agent 守卫 + 收尾

- [x] **7-1：更新 architecture-guard.md** `[S]`（早期 Phase 已预先完成）
  - 规则 4（BuilderConversation/ProjectFile 约束）+ 规则 7（文件存储）+ 检查 5（Builder Agent）
- [x] **7-2：更新 code-reviewer.md** `[S]`（早期 Phase 已预先完成）
  - 构建 Agent 相关小节：LLM 响应 sanitize + 文件上传校验 + 空字段校验 + 幂等性 + system prompt 常量
- [x] **7-3：更新 architecture.md** `[M]`
  - 实体关系（+ProjectFile/BuilderConversation）+ 表结构（sparring_prompt/judge_prompt_segment/新表）+ API（文件/对话/构建Agent）+ 引擎（Builder Agent/File Parser/Prompt Defaults）+ 级联规则 + 路由（ProjectLayout）+ 目录（layouts/）
- [x] **7-4：更新 testing.md** `[S]`
  - 必测场景补充 3 项 + 文件位置补充 4 个新测试文件 + Fixture 说明（MockLLMAdapter + 工厂）
- [x] **7-5：更新 conventions.md** `[S]`
  - 前端目录补充 builder-agent/ + layouts/ + 新增文件存储规范 + 构建 Agent 组件规范
- [x] **7-6：更新 backlog.md** `[S]`
  - 仪表盘重算（14→11）+ Done 条目迁入归档（UX-01/04/05/09/10、AR-01/02/03、EN-01/02/03/04、FT-01/03）+ 日期更新
- [x] **7-7：更新 CLAUDE.md** `[S]`
  - 版本状态更新为 Phase 7 完成
- [x] **7-8：最终验证** `[S]`
  - 双 Agent 审查通过，修复 8 项（表结构精度 3 项 + 级联描述 2 项 + LLM 接口签名 + 测试文件名 + 错误处理规范）

**验证**：双 Agent 审查通过 ✓ → 文档完整 ✓

---

### 自动化测试策略

| 类别 | 测试文件 | 覆盖范围 | 触发 Phase |
|------|---------|---------|-----------|
| 更新 | `conftest.py` | fixtures 适配新字段 | 1 |
| 更新 | `test_sparring_runner.py` | 新 prompt 格式 + first_message 回退 | 2 |
| 更新 | `test_judge_runner.py` | 新 eval 格式 + 旧 snapshot 兼容 | 2 |
| 新增 | `test_prompt_defaults.py` | 默认 prompt 非空 + 关键内容 | 2 |
| 新增 | `test_project_file_service.py` | 上传/删除/类型校验 | 4 |
| 新增 | `test_builder_agent.py` | prompt 组装 + 输出解析 + 配置写入 | 4+6 |

原则：后端改动必须 `pytest`，前端改动必须 `tsc --noEmit`，每个 Phase 完成后跑 code-reviewer + architecture-guard。

---

## 交接备注

**Session #34 (2026-03-14)**：暖绿主题迁移（Humanloop 风格）。

- 新建 `frontend/src/theme/themeConfig.ts` — 集中定义 Ant Design token + SEMANTIC_COLORS 语义色常量
- 布局从顶部深色 Header 迁移至左侧固定 Sider（232px，暖奶油底色）
- 全局色彩：森林绿主色 `#2d7a4e` + 暖奶油底色 `#f3f1ec`，无紫色元素
- 17 个文件（1 新建 + 16 修改），涉及 theme/layouts/pages/components
- 修复 Sider flex+overflow 冲突（分离到内层 div）
- 修复 Tag 标签对比度（显式指定 colorSuccessBg/colorErrorBg map token）
- conventions.md 新增前端样式规范（颜色集中管理）

**Session #33 (2026-03-13)**：文档体系 review + 修复 10 项问题。

- 追踪 uv.lock + 二期 PRD，design-preview 加入 .gitignore
- conventions.md 新增提交前检查未追踪文件约定 + 部署规范段落
- CLAUDE.md 精简开发规则（去重）、补 deploy 索引、更新当前状态
- conventions.md 目录职责精简（指向 architecture.md）
- architecture.md LLM 接口签名同步代码
- testing.md 运行命令更新为 uv
- .gitignore 补充 .pytest_cache/.mypy_cache/.coverage/htmlcov
- p2-interaction-redesign.md 移入 archive
- v1.0 交接备注折叠

**Session #32 (2026-03-12)**：v1.0 Phase 7 文档 + Agent 守卫 + 收尾完成。v1.0 二期全部 Phase 完成。

<details>
<summary>v1.0 交接详情（Session #26-#32）</summary>

**Session #32**：Phase 7 文档收尾 — architecture/testing/conventions/backlog 全面更新 + 双 Agent 审查修复 8 项

**Session #31**：Phase 6 构建 Agent 智能层 — System Prompt + 结构化输出解析（XML 标签 + chat_json 重试）+ 配置写入（直接 ORM + 单次 commit）+ 95 个测试 + 前端确认卡片联调 + 代码审查修复 5 项

**Session #30**：Phase 5 构建 Agent 前端 UI — 悬浮球 + 对话面板（Optimistic update）+ 消息气泡（XSS 防护）+ 确认卡片 + 文件管理 + ProjectLayout 布局集成

**Session #29**：Phase 4 新增后端 API — 项目文件 + 构建对话 + 构建 Agent 聊天 + 文件解析器 + 代码审查修复 6 项

**Session #28**：Phase 2 + Phase 3 — 核心引擎适配（默认 Prompt + 新字段注入）+ 前端适配（用例折叠面板 + 默认 Prompt 展示）

**Session #27**：Phase 1 数据模型迁移 — Alembic 迁移 + Models/Schemas/Types/Fixtures 适配 + 旧 snapshot 兼容

**Session #26**：v1.0 二期规划 — 7 Phase 42 任务

</details>

---

<details>
<summary>v0.3 稳定性与体验修复（已完成） — Phase BugFix + P1 + P2 + Deploy，Session #17-#25</summary>

> 修复 P0 级 bug + 核心体验问题 + 交互重设计 + 生产部署准备。

- **Phase BugFix**（3 任务 ✅）：批测 running 恢复机制、对话剧场布局修复、模型配置引导
- **Phase P1**（5 任务 ✅）：批测删除、Service 层补全、Token 编辑体验、轮次编号、datetime 修复
- **Phase P2**（6 任务 ✅）：批测多选、裁判配置查看态、模型配置查看态、Agent Modal 分组、pass_threshold float、chat_json 清理
- **Phase Deploy**（7 任务 ✅）：Docker Compose 生产化、自动迁移、Nginx 加固、健康检查、备份脚本、部署文档、安全加固

</details>

<details>
<summary>v0.2 架构重构（已完成） — Phase 1-5 + UX 修复，Session #9-#16</summary>

> 基于 `docs/prd/eval-platform-mvp-spec-v2.md`，将 Tab 式工作台升级为页面下钻式架构。
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
