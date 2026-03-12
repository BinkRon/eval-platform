"""Shared test fixtures: mock LLM adapter and model factories."""
import uuid
from types import SimpleNamespace

import pytest

from app.llm.base import LLMAdapter


# ---------------------------------------------------------------------------
# MockLLMAdapter
# ---------------------------------------------------------------------------

class MockLLMAdapter(LLMAdapter):
    """In-memory LLM mock that returns pre-configured responses in FIFO order."""

    def __init__(self):
        # Skip real LLMAdapter.__init__ which requires api_key/model
        self.api_key = "test-key"
        self.model = "test-model"
        self.base_url = None
        self.timeout = 60.0
        self.max_retries = 2

        self.chat_responses: list[str] = []
        self.chat_json_responses: list[dict | Exception] = []
        self.chat_call_count = 0
        self.chat_json_call_count = 0
        self.chat_call_args: list[dict] = []
        self.chat_json_call_args: list[dict] = []

    async def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=2048) -> str:
        self.chat_call_count += 1
        self.chat_call_args.append({
            "messages": messages,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        if not self.chat_responses:
            raise ValueError("MockLLMAdapter: chat_responses exhausted")
        return self.chat_responses.pop(0)

    async def chat_json(self, messages, system_prompt=None, temperature=0.0,
                        max_tokens=2048) -> dict:
        self.chat_json_call_count += 1
        self.chat_json_call_args.append({
            "messages": messages,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        if not self.chat_json_responses:
            raise ValueError("MockLLMAdapter: chat_json_responses exhausted")
        resp = self.chat_json_responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp


@pytest.fixture
def mock_llm() -> MockLLMAdapter:
    return MockLLMAdapter()


# ---------------------------------------------------------------------------
# Factory fixtures — use SimpleNamespace to avoid SQLAlchemy instrumentation
# ---------------------------------------------------------------------------

@pytest.fixture
def project_factory():
    def _create(**kwargs):
        defaults = {
            "id": uuid.uuid4(),
            "name": "Test Project",
            "description": "A test project",
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)
    return _create


@pytest.fixture
def agent_version_factory(project_factory):
    def _create(**kwargs):
        if "project_id" not in kwargs:
            kwargs["project_id"] = project_factory().id
        defaults = {
            "id": uuid.uuid4(),
            "name": "v1.0",
            "description": "Test agent",
            "endpoint": "https://example.com/chat",
            "method": "POST",
            "auth_type": None,
            "auth_token": None,
            "request_template": None,
            "response_path": "$.reply",
            "has_end_signal": False,
            "end_signal_path": None,
            "end_signal_value": None,
            "response_format": "json",
            "connection_status": "untested",
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)
    return _create


@pytest.fixture
def test_case_factory(project_factory):
    def _create(**kwargs):
        if "project_id" not in kwargs:
            kwargs["project_id"] = project_factory().id
        defaults = {
            "id": uuid.uuid4(),
            "name": "Test Case 1",
            "sparring_prompt": "## 角色背景\nA customer with a pending order\n\n## 行为特征\nPolite but impatient",
            "first_message": "Hello, I need help with my order.",
            "max_rounds": 5,
            "sort_order": 0,
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)
    return _create


@pytest.fixture
def checklist_item_factory():
    def _create(**kwargs):
        defaults = {
            "id": uuid.uuid4(),
            "judge_config_id": uuid.uuid4(),
            "content": "Agent greeted the user",
            "level": "must",
            "sort_order": 0,
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)
    return _create


@pytest.fixture
def eval_dimension_factory():
    def _create(**kwargs):
        defaults = {
            "id": uuid.uuid4(),
            "judge_config_id": uuid.uuid4(),
            "name": "Helpfulness",
            "judge_prompt_segment": "How helpful was the agent\n\n## 评分标准\n- 3分（优秀）：Very helpful\n- 2分（合格）：Somewhat helpful\n- 1分（不合格）：Not helpful",
            "sort_order": 0,
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)
    return _create


@pytest.fixture
def judge_config_factory(checklist_item_factory, eval_dimension_factory):
    def _create(checklist_items=None, eval_dimensions=None, **kwargs):
        config_id = kwargs.pop("id", uuid.uuid4())
        defaults = {
            "id": config_id,
            "project_id": uuid.uuid4(),
            "pass_threshold": 2.0,
        }
        defaults.update(kwargs)

        if checklist_items is None:
            checklist_items = [
                checklist_item_factory(judge_config_id=config_id, content="Greeted user", level="must"),
                checklist_item_factory(judge_config_id=config_id, content="Provided solution", level="important"),
            ]
        if eval_dimensions is None:
            eval_dimensions = [
                eval_dimension_factory(judge_config_id=config_id, name="Helpfulness"),
                eval_dimension_factory(judge_config_id=config_id, name="Accuracy"),
            ]

        defaults["checklist_items"] = checklist_items
        defaults["eval_dimensions"] = eval_dimensions
        return SimpleNamespace(**defaults)
    return _create


@pytest.fixture
def sample_conversation():
    return [
        {"role": "user", "content": "Hello, I need help with my order."},
        {"role": "assistant", "content": "Hello! I'd be happy to help with your order. Could you share the order number?"},
        {"role": "user", "content": "My order number is #12345."},
        {"role": "assistant", "content": "Thank you! I found order #12345. It is currently being processed."},
    ]
