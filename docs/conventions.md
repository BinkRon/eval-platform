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
- 写操作使用 `async with db.begin()` 确保事务
- 查询使用 `select()` + `where()` 组合
- ID 使用 UUID，由数据库生成或 Python uuid4
- 时间戳使用 `func.now()` 让数据库生成

### 错误处理

| 场景 | 处理方式 |
|------|---------|
| 资源不存在 | raise HTTPException(404, detail="Project not found") |
| 参数校验失败 | Pydantic 自动处理（422） |
| 业务规则违反 | raise HTTPException(400, detail="具体原因") |
| 数据库异常 | 捕获 IntegrityError，返回 400 |
| LLM 调用失败 | 服务内部处理，返回结构化错误 |

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
