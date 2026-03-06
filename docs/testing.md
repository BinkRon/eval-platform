# 评测平台 — 测试指南

> 本文档定义测试策略和编写规范。

## 测试策略

### 后端：分层测试

| 层 | 测什么 | 框架 | 优先级 |
|----|--------|------|--------|
| Service 层 | 核心业务逻辑（对练、裁判、调度） | pytest + pytest-asyncio | **必测** |
| API 层 | 路由参数校验、HTTP 状态码 | pytest + httpx (TestClient) | 推荐 |
| LLM 适配层 | 适配器接口行为 | pytest + mock | 推荐 |

**必测场景**（出错代价高的部分）：
- 对练运行器的三种终止条件
- 裁判运行器的 prompt 组装和 JSON 解析
- 批测调度器的并发控制和进度追踪
- 通过判定逻辑（must_pass checklist 全通过 + eval 均分 ≥ 阈值）
- Agent Client 的模板替换和 JSONPath 解析

**可不测**（简单 CRUD）：
- 项目/用例/版本的基本增删改查（Pydantic + SQLAlchemy 已保证）

### 前端：MVP 阶段暂不强制

前端以手动测试为主。如后续需要，使用 Vitest + React Testing Library。

## 后端测试规范

### 文件位置

```
backend/tests/
├── conftest.py              # 公共 fixture（测试数据库、测试客户端）
├── test_services/
│   ├── test_agent_client.py
│   ├── test_sparring_runner.py
│   ├── test_judge_runner.py
│   └── test_batch_scheduler.py
├── test_api/
│   ├── test_projects.py
│   ├── test_agent_versions.py
│   └── test_batch_tests.py
└── test_llm/
    ├── test_anthropic.py
    └── test_openai_adapter.py
```

### 公共 Fixture

```python
# conftest.py
@pytest.fixture
async def db():
    """创建测试数据库会话（每个测试独立事务，测试结束回滚）"""

@pytest.fixture
async def client(db):
    """创建 FastAPI 测试客户端，注入测试 db"""

@pytest.fixture
def mock_llm():
    """Mock LLM 适配器，返回预设回复"""

@pytest.fixture
async def sample_project(db):
    """创建一个完整的测试项目（含 Agent 版本、用例、裁判配置）"""
```

### 编写要求

- LLM 调用必须 mock，不在测试中真正调用 API
- Agent API 调用必须 mock（使用 httpx mock 或 respx）
- 测试数据使用 fixture 工厂，不硬编码
- 异步测试使用 `@pytest.mark.asyncio`

### 运行

```bash
cd backend
pip install -e ".[dev]"   # 安装开发依赖
pytest                     # 运行全部测试
pytest -v                  # 详细输出
pytest tests/test_services/  # 只跑 service 测试
pytest -x                  # 遇到第一个失败就停止
```
