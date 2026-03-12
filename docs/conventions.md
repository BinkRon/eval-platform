# 评测平台 — 代码规范

> 本文档随开发过程逐步补充。每当建立新的模式或约定时，在此记录。

## 文件命名

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| Python 模块 | snake_case | `agent_version.py`, `batch_scheduler.py` |
| React 组件 | PascalCase | `ProjectList.tsx`, `BatchTestDetail.tsx` |
| React hooks | camelCase | `useProjects.ts`, `useBatchTest.ts` |
| TypeScript 类型 | camelCase | `types.ts`, `api.ts` |
| API 调用层 | camelCase | `projects.ts`, `batchTests.ts` |

## 目录职责

### 后端

- `app/models/` — SQLAlchemy 数据模型，每个实体一个文件
- `app/schemas/` — Pydantic 请求/响应模型，每个资源一个文件
- `app/api/` — FastAPI 路由处理，每个资源一个文件（仅做参数校验 + 调用 service）
- `app/services/` — 核心业务逻辑（对练运行器、裁判运行器、批测调度、Agent 客户端）
- `app/llm/` — LLM 适配层（base 接口 + 各厂商实现 + 工厂方法）
- `app/utils/` — 通用工具函数

### 前端

- `src/pages/` — 页面组件，对应路由
- `src/components/` — 按模块分子目录（agent-version/, experiment/, batch-test/ 等）
- `src/components/shared/` — 跨模块复用的纯 UI 组件（无业务逻辑依赖）
- `src/components/builder-agent/` — 构建 Agent 组件（悬浮球、对话面板、确认卡片、文件管理）
- `src/layouts/` — 布局组件（ProjectLayout 等，包裹 Outlet + 全局浮层）
- `src/api/` — API 调用封装（每个资源一个文件）
- `src/hooks/` — 自定义 hooks（TanStack Query 封装）
- `src/types/` — TypeScript 类型定义

## 后端开发规范

### API 路由

```python
# 路由层只做参数校验和调用 service，不放业务逻辑
@router.post("/", response_model=ProjectResponse)
async def create_project(data: CreateProjectRequest, db: AsyncSession = Depends(get_db)):
    return await project_service.create(db, data)
```

### 数据库操作

- 使用 SQLAlchemy ORM，不手写原生 SQL
- 写操作使用手动 `await db.commit()`（注：asyncpg 与 `async with db.begin()` 存在事务冲突问题）
- 查询使用 `select()` + `where()` 组合
- ID 使用 UUID，由数据库生成或 Python uuid4
- 时间戳使用 `func.now()` 让数据库生成

### 错误处理

**Service 层**：抛出领域异常，由 `main.py` 全局处理器统一转换为 HTTP 响应。

| 场景 | 处理方式 |
|------|---------|
| 资源不存在 | raise NotFoundError("Project not found") → 404 |
| 参数/业务规则违反 | raise ValidationError("具体原因") → 400 |
| 资源冲突（如重名） | raise ConflictError("供应商已存在") → 409 |
| 参数校验失败 | Pydantic 自动处理（422） |
| 数据库异常 | 捕获 IntegrityError，转为 ValidationError |
| LLM 调用失败 | 服务内部处理，返回结构化错误 |

**API 层**：仅做参数解析 + 调用 service，不直接 raise HTTPException。

### LLM 适配层

```python
# 所有 LLM 调用通过统一接口
adapter = create_llm_adapter(provider_name, api_key, model_name)
reply = await adapter.chat(messages, system_prompt, temperature, max_tokens)
```

- 不在 service 层直接 import 厂商 SDK
- 新增厂商只需：实现 LLMAdapter 子类 + 在 factory 注册

## 前端开发规范

### 数据获取

```typescript
// 使用 TanStack Query 封装
export function useProjects() {
  return useQuery({ queryKey: ['projects'], queryFn: projectApi.list })
}

// 写操作后自动刷新
export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: projectApi.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects'] })
  })
}
```

### 组件原则

- 页面组件负责数据获取和布局，不包含复杂业务逻辑
- 表单使用 Ant Design Form 组件，统一受控模式
- 列表/表格使用 Ant Design Table 组件

### 错误处理

| 场景 | 处理方式 |
|------|---------|
| API 请求失败 | `message.error(error.detail)` |
| 表单校验失败 | Ant Design Form 内联提示 |
| 删除操作 | Modal.confirm 二次确认 |

## Git 规范

### 提交时机
- 每完成一个任务提交一次
- 功能关联的多模块变更合并为一个 commit

### Commit Message 格式
- 格式：`<类型>: <简洁中文描述>`（不超过 50 字）
- 禁止使用 `git add .` 或 `git add -A`，明确指定文件

| 类型 | 适用场景 | 示例 |
|------|---------|------|
| feat | 新增功能 | `feat: 添加项目列表页` |
| fix | 修复 bug | `fix: 修复批测进度轮询不更新` |
| refactor | 重构 | `refactor: 重构 LLM 适配层接口` |
| style | 样式 | `style: 调整批测详情页布局` |
| docs | 文档 | `docs: 更新开发进度` |
| chore | 配置 | `chore: 配置 Docker Compose` |
| db | 数据库 | `db: 新增 eval_dimensions 表` |
| test | 测试 | `test: 补充裁判运行器单元测试` |

## 安全编码规范

### 外部 URL 校验
- 所有用户提供的 URL（如 Agent endpoint）在请求前必须经过 SSRF 防护校验
- 拒绝私有 IP 段（10.x、172.16-31.x、192.168.x、127.x、169.254.x）
- 只允许 http/https scheme

### 错误信息脱敏
- 面向用户的错误信息不得包含内部 IP 地址、堆栈跟踪、数据库连接信息
- 使用正则替换敏感信息为通用提示

### 敏感数据处理
- API 响应中不返回 auth_token 原文，仅返回 `auth_token_set: bool`
- 密码、API Key 等敏感字段使用 `SecretStr` 或在 schema 中排除

## 容器安全规范

- Dockerfile 使用非 root 用户运行应用（`USER appuser`）
- 不在镜像中存储敏感文件（.env、密钥文件）
- 使用 `.dockerignore` 排除不必要文件

## Agent-Friendly API 设计规范

> 设计原则：API 不仅服务人类开发者，也服务 AI Agent。好的 API 自描述能力让 Agent 能直接理解系统能做什么、该怎么用，无需额外的操作手册。

### Pydantic Schema — 必须自描述

**每个 Field 必须包含 `description`**，说明这个字段的语义、用途和业务含义：

```python
# ✅ 正确
sparring_prompt: str = Field(
    min_length=1,
    description="对练模型的角色扮演指令，支持 markdown，将注入对练模型的 system prompt"
)
concurrency: int = Field(
    default=3, ge=1, le=20,
    description="并行执行的测试用例数量"
)

# ❌ 错误 — 只有约束，没有语义
sparring_prompt: str = Field(min_length=1)
concurrency: int = Field(default=3, ge=1, le=20)
```

**枚举/有限值字段必须说明每个取值的含义：**

```python
level: str = Field(
    description="检查项级别。required: 红线项，违反即不通过；important: 影响评分但不一票否决"
)
status: str = Field(
    description="批测状态。pending: 等待执行；running: 执行中；completed: 已完成；failed: 执行失败"
)
```

**关键字段提供 `example`**（尤其是自由文本字段和复杂结构）：

```python
message: str = Field(
    min_length=1,
    description="用户发送给构建助手的消息",
    examples=["请生成 5 条关于理财推荐场景的测试用例"]
)
```

**Schema 类必须有 docstring**，说明整个模型的用途：

```python
class BatchTestCreate(BaseModel):
    """发起批测的请求参数。指定 Agent 版本和并发度，可选过滤用例和裁判配置范围。"""
    ...
```

### FastAPI 路由 — 必须有操作描述

**每个路由函数必须有 docstring**，FastAPI 会自动将其作为 OpenAPI 的 operation summary：

```python
@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """创建评测项目。"""
    return await project_service.create(db, data)

@router.get("/{project_id}/readiness", response_model=ConfigReadiness)
async def get_readiness(project_id: UUID, db: AsyncSession = Depends(get_db)):
    """获取项目配置就绪状态，返回各模块的就绪情况和缺失项。"""
    return await project_service.get_config_readiness(db, project_id)
```

### 错误响应 — 必须可编程消费

**使用 error_code 区分错误类型**（已有基础设施，需启用）：

```python
# Service 层抛出时带 error_code
raise ValidationError("缺少对练模型配置", error_code="MISSING_SPARRING_MODEL")
raise NotFoundError("项目不存在", error_code="PROJECT_NOT_FOUND")
```

### 命名一致性 — 已有实践，继续保持

- 同一概念在 Model / Schema / API / 前端 / 文档中使用同一个名字
- 语义化命名，不使用缩写（`agent_version` 而非 `av`）
- snake_case 贯穿后端所有层级

### SQLAlchemy Model — 建议自描述

**字段级 `comment` 参数**（写入数据库 column comment，增强数据库自身的可读性）：

```python
sparring_prompt: Mapped[str] = mapped_column(
    Text, nullable=False,
    comment="对练模型的角色扮演指令，markdown 格式"
)
```

**类级 docstring**：

```python
class TestCase(UUIDPrimaryKey, TimestampMixin, Base):
    """测试用例。定义对练场景的角色设定，驱动对练模型模拟特定类型的用户。"""
    ...
```

## 文件存储规范

- 存储路径通过环境变量 `FILE_STORAGE_PATH` 配置，不可硬编码
- 上传文件类型白名单：PDF / DOCX / TXT / MD / XLSX / CSV
- 上传文件大小上限：20MB，使用 Content-Length 前置校验
- 文件名净化：去除路径分隔符，防止路径遍历攻击
- API 响应中不暴露 `storage_path`（内部字段）
- 删除操作顺序：先删 DB 记录，后删物理文件（物理删除失败仅 log 不抛异常）

## 构建 Agent 组件规范

- 悬浮球 `FloatingButton` 固定在右下角，projectId 变化时自动收起
- 对话面板 `ChatPanel` 使用 Optimistic Update：发送时立即显示用户消息，成功后追加助手消息，失败按 snapshot 长度回滚
- 消息气泡 `MessageBubble` 使用 react-markdown + rehype-sanitize 渲染（XSS 防护）
- 确认卡片组件（GenerateConfirmCard / OverwriteConfirmCard / ClarifyCard）由后端 card_type 驱动渲染
- 文件管理 `ProjectFileManager` 使用 Popover 浮层，前端校验扩展名和大小

## 环境配置规范

- 项目根目录提供 `.env.example` 模板，列出所有必需环境变量
- 敏感配置（API Key、数据库密码）通过环境变量注入，不硬编码
- 环境变量命名：大写 + 下划线，如 `DATABASE_URL`、`ANTHROPIC_API_KEY`
