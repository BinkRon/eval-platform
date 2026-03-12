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

- [ ] **7-1：更新 architecture-guard.md** `[S]`
  - 新增：Builder Agent LLM 适配层规则 + 文件存储可配置规则 + 新实体约束
- [ ] **7-2：更新 code-reviewer.md** `[S]`
  - 新增：LLM 响应 sanitize + 文件上传校验 + 空字段校验 + 幂等性检查
- [ ] **7-3：更新 architecture.md** `[M]`
  - 表结构 + API 设计 + 核心引擎 + 级联删除规则
- [ ] **7-4：更新 testing.md** `[S]`
  - 新增测试范围 + fixtures 说明
- [ ] **7-5：更新 conventions.md** `[S]`
  - builder-agent/ 组件规范 + 文件存储规范
- [ ] **7-6：更新 backlog.md** `[S]`
  - 二期相关条目状态流转
- [ ] **7-7：更新 CLAUDE.md** `[S]`
  - 版本号 + 文档索引 + 开发规则
- [ ] **7-8：最终验证** `[S]`
  - code-reviewer + architecture-guard 双 Agent 审查通过

**验证**：双 Agent 审查通过 ✓ → 文档完整 ✓

---

### 自动化测试策略

| 类别 | 测试文件 | 覆盖范围 | 触发 Phase |
|------|---------|---------|-----------|
| 更新 | `conftest.py` | fixtures 适配新字段 | 1 |
| 更新 | `test_sparring_runner.py` | 新 prompt 格式 + first_message 回退 | 2 |
| 更新 | `test_judge_runner.py` | 新 eval 格式 + 旧 snapshot 兼容 | 2 |
| 新增 | `test_prompt_defaults.py` | 默认 prompt 非空 + 关键内容 | 2 |
| 新增 | `test_project_file.py` | 上传/删除/类型校验 | 4 |
| 新增 | `test_builder_agent.py` | prompt 组装 + 输出解析 + 配置写入 | 4+6 |

原则：后端改动必须 `pytest`，前端改动必须 `tsc --noEmit`，每个 Phase 完成后跑 code-reviewer + architecture-guard。

---

## 交接备注

**Session #31 (2026-03-12)**：v1.0 Phase 6 构建 Agent 智能层完成。

Phase 6 构建 Agent 智能层：
- 6-1 System Prompt：完整角色定义 + 用例生成 Skill（PRD §4.2）+ 裁判配置生成 Skill（PRD §4.3）
- 6-2 结构化输出解析：`<generated_config>` XML 标签 regex 提取 + `chat_json` 重试 fallback + 卡片类型检测 + 标签残留清除
- 6-3 配置写入：直接 ORM `db.add()` + 单次 `db.commit()`（避免 service 层逐条 commit 导致部分写入）；level 映射 required→must / important→should + 未知值安全回退 "should"
- 6-4 测试：95 个测试全部通过，覆盖 prompt 内容、config block 解析（7 case）、card 构建、chat 流程（含 retry）、apply 写入（append/replace/level fallback/validation）
- 前端联调：ChatPanel 接入 card_type/card_data → GenerateConfirmCard/OverwriteConfirmCard；确认按钮 loading 态禁用；结构化 count 字段替代字符串前缀匹配
- 代码审查修复 5 项：事务一致性（直接 ORM）、level_map fallback 逻辑、标签残留清除、缺失字段 validation、按钮 loading
- 下一步：Phase 7 文档 + Agent 守卫 + 收尾

**Session #30 (2026-03-12)**：v1.0 Phase 5 构建 Agent 前端 UI 完成。

Phase 5 构建 Agent 前端 UI：
- API 层 + Hooks：builderAgent（120s timeout）/ builderConversation / projectFiles，类型定义迁移到 types/builderAgent.ts
- 悬浮球：右下角固定定位，projectId 变化自动收起面板
- 对话面板：标题栏（📁 文件管理 + 模型选择 + 清空确认 + 收起）+ 消息流 + 输入区（Enter 发送 / Shift+Enter 换行）
- 消息气泡：用户右对齐蓝底 / 助手左对齐绿底，react-markdown + remark-gfm + rehype-sanitize（XSS 防护）
- Optimistic update：发送时立即显示 user 消息 → 成功追加 assistant → 失败按 snapshot 长度回滚；移除 hook 中 invalidateQueries 避免 double-update
- 确认卡片：GenerateConfirmCard / OverwriteConfirmCard / ClarifyCard 三个 UI 组件（Phase 6 接入智能层）
- 文件管理：Popover 浮层 + Upload 前端校验 + Popconfirm 删除 + 按 file.id 精确匹配 loading
- 布局集成：ProjectLayout（Outlet + FloatingButton）+ App.tsx 路由嵌套
- 新增依赖：react-markdown / remark-gfm / rehype-sanitize
- tsc --noEmit 通过、双 Agent 审查通过（修复 6 项）
- 下一步：Phase 6 构建 Agent 智能层

**Session #29 (2026-03-12)**：v1.0 Phase 4 新增后端 API 完成。

Phase 4 新增后端 API：
- 项目文件 API：upload/list/delete + 白名单校验 + 20MB 限制 + 路径遍历防护 + storage_path 脱敏
- 构建对话 API：get_or_create/append_message/clear + JSONB 持久化 + MessageData 类型约束
- 构建 Agent 聊天 API：项目上下文加载 + LLM 适配层调用 + 消息持久化（先 LLM 后写入，防孤立消息）
- 文件解析器：PDF/DOCX/TXT/MD/XLSX/CSV 文本提取
- 新增依赖：aiofiles/pypdf/python-docx/openpyxl/python-multipart
- 代码审查修复 6 项：文件名净化、os.remove 异常处理、storage_path 脱敏、前置大小校验、DB 先删后物理删、LLM 失败不留孤立消息
- pytest 73 passed、双 Agent 审查通过
- 下一步：Phase 5 构建 Agent 前端 UI

**Session #28 (2026-03-12)**：v1.0 Phase 2 + Phase 3 完成。

Phase 3 前端适配：
- TestCaseTab：sparring_prompt TextArea 增大 + 高级配置折叠面板（Collapse destroyInactivePanel={false}）
- ModelConfigTab：查看态显示默认 Prompt +「系统默认」标签；编辑态简短 placeholder 提示
- 前端默认 Prompt 常量与后端 prompt_defaults.py 严格对齐（含 markdown 粗体、完整文本）
- JudgeConfigTab + DialogTheater 已在 Phase 1 适配完成
- tsc --noEmit 通过、pytest 46 passed、双 Agent 审查通过（修复前后端不一致问题）
- 下一步：Phase 4 新增后端 API

Phase 2 核心引擎适配：

- 2-1/2-2/2-4 已在 Phase 1 额外适配中完成（sparring_prompt 注入、judge_prompt_segment + 旧 snapshot 兼容、judge_config_service）
- 新建 `prompt_defaults.py`：对练/裁判默认 System Prompt（PRD §3.4），[END] 由 `_build_persona_prompt` 追加避免重复
- `batch_scheduler.py`：system_prompt 为空时 fallback 默认值
- 新增 6 个测试：prompt 注入格式、first_message=None 回退、旧 snapshot 兼容、judge_prompt_segment 优先、默认 prompt 内容
- 重构 MockLLMAdapter.chat_json 原生支持 Exception，消除 2 处 monkey-patch 重复
- pytest 46 passed、tsc --noEmit 通过、双 Agent 审查通过
- 下一步：Phase 3 前端适配

**Session #27 (2026-03-12)**：v1.0 Phase 1 数据模型迁移完成。

- Alembic 迁移脚本：TestCase/EvalDimension 字段重构 + project_files/builder_conversations 新表
- SQLAlchemy Models、Pydantic Schemas、TypeScript Types、测试 Fixtures 全部适配
- 额外适配 4 个 service（sparring_runner/judge_runner/batch_test_service/judge_config_service）+ 2 个前端组件
- judge_runner 保留旧 snapshot 向后兼容（hasattr fallback）
- 代码审查修复：迁移空值 fallback 改为有意义默认值、Schema 加 min_length 校验、judge_runner 兼容逻辑加固
- pytest 30 passed、tsc --noEmit 通过
- 下一步：Phase 2 核心引擎适配

**Session #26 (2026-03-12)**：v1.0 二期规划完成。

- 阅读二期 PRD（`docs/prd/eval-platform-phase2-spec.md`），分析变更范围
- 设计 7 Phase 执行计划（41 个任务），按依赖关系排序
- 更新 progress.md（v0.3 折叠 + v1.0 任务清单）、CLAUDE.md、architecture-guard.md、code-reviewer.md
- 下一步：Phase 1 数据模型迁移

**Session #25 (2026-03-11)**：补充本地开发到远程 Docker 发布的标准化流程。

- 在 `deploy/README.md` 新增”推荐工作流：本地开发 → 远程发布”章节
- 新增 `deploy/release.sh` 远程发布脚本：支持拉取最新代码、重建生产容器、执行 backend 健康检查和 frontend 入口检查
- 明确区分本地 `docker-compose.yml` 与远程 `docker-compose.prod.yml` 的用途
- 补充 detached HEAD / 指定 commit 回滚场景的发布说明，避免默认 `git pull` 失败
- 补充发布前检查、线上冒烟、环境变量对齐、migration 管理、禁止在线上容器手改代码、回滚策略
- 目标：减少”本地验证通过，但远程 Docker 运行效果不一致”的问题

**Session #24 (2026-03-10)**：生产部署准备全部完成。

- 新增 `docker-compose.prod.yml`（生产专用，与开发 `docker-compose.yml` 分离）
- 新增 `backend/entrypoint.sh`（启动前自动跑迁移）、`.env.production.example`（环境变量模板）
- 新增 `deploy/backup.sh`（pg_dump 备份脚本）、`deploy/README.md`（CentOS 部署指南）
- 改造 `backend/Dockerfile`、`frontend/nginx.conf`、`backend/app/main.py`（健康检查）、`.gitignore`、`backend/.dockerignore`
- 代码审查修复：`text()` → `select(literal(1))`、backup.sh source 注入、CORS 模板、backend 端口不暴露、nginx assets 安全头
- 下一步：在服务器上执行部署（参见 `deploy/README.md`）

**Session #23 (2026-03-09)**：P2-2a/P2-2b/P2-2c 配置展示优化全部完成。

- P2-2a：裁判配置 Table+Card 查看态，view/edit 切换，首次无数据自动编辑态
- P2-2b：模型配置纵向双 Card 堆叠，独立 view/edit，dirty 状态隔离（Set 追踪），scoped validateFields
- P2-2c：Agent 版本 Modal Divider 三段分组
- 代码审查修复：enterEdit 空 config 防护、dirty 互覆盖、validateFields 跨 card 校验、syncForm 定义顺序
- Phase P2 全部完成（6/6），UX-09 可标记 Done

**Session #22 (2026-03-09)**：P2-1 发起批测 Modal 多选。

- 后端 BatchTestCreate 新增 4 个可选字段（test_case_ids/checklist_item_ids/eval_dimension_ids/pass_threshold）
- validate_and_create 按选中 ID 过滤，过滤后存入 config_snapshot
- batch_scheduler _load_context 从 snapshot 读取测试用例 ID 和裁判配置（SimpleNamespace 替代 JudgeConfig ORM）
- 前端 Modal 增加三个 Select multiple（默认全选）+ 通过阈值 InputNumber + 模型配置只读区
- 全选时不传 ID（后端默认全量），部分选中传选中列表
- 代码审查修复：snapshot 空值不回退全量、异常处理、类型标注、校验错误提示
- 下一步：P2-2a（裁判配置查看态）→ P2-2b → P2-2c

**Session #21 (2026-03-09)**：Phase P2 交互重设计 — 回退 + PRD + 工程修复。

- 用户对 P2 交互设计不满意，回退 74d5760 和 4a045a1 两个 commit
- 重新单独提交工程修复：P2-3（pass_threshold float）、P2-4（chat_json 参数清理）
- 建立 `docs/prd/` 目录，编写 PRD：`p2-interaction-redesign.md`
- 设计要点：发起批测保持 Modal + Select multiple 多选；裁判配置 Table+Card 查看态；模型配置纵向+分别编辑
- 更新 CLAUDE.md 文档索引、backlog UX-09/FT-03 关联 PRD、progress.md P2 任务清单
- P2-3/P2-4 已完成，P2-1/P2-2a/P2-2b/P2-2c 待实现
- 下一步：按 PRD 实现 P2-1 → P2-2a → P2-2b → P2-2c

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
