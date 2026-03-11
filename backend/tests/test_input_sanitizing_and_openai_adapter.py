from types import SimpleNamespace

import pytest

from app.llm.openai_adapter import _extract_chat_content, _normalize_model_name
from app.schemas.model_config import ModelConfigUpdate
from app.schemas.provider import ProviderCreate, ProviderUpdate


def test_model_config_update_strips_model_names():
    payload = ModelConfigUpdate(
        sparring_provider=" zhuiyi ",
        sparring_model=" Mistral-Small-3.1-24B-Instruct-2503 ",
        judge_provider=" zhuiyi ",
        judge_model=" Qwen3-235B-A22B-Instruct-2507 ",
    )

    assert payload.sparring_provider == "zhuiyi"
    assert payload.sparring_model == "Mistral-Small-3.1-24B-Instruct-2503"
    assert payload.judge_provider == "zhuiyi"
    assert payload.judge_model == "Qwen3-235B-A22B-Instruct-2507"


def test_provider_create_strips_available_models_and_api_key():
    payload = ProviderCreate(
        provider_name="zhuiyi",
        api_key=" test-key ",
        base_url="http://example.com/v1",
        available_models=[" Qwen3-Plus ", " ", " Mistral-Small-3.1-24B-Instruct-2503"],
    )

    assert payload.api_key == "test-key"
    assert payload.available_models == [
        "Qwen3-Plus",
        "Mistral-Small-3.1-24B-Instruct-2503",
    ]


def test_provider_update_strips_available_models():
    payload = ProviderUpdate(
        available_models=[" Qwen3-235B-A22B-Instruct-2507 ", ""],
    )

    assert payload.available_models == ["Qwen3-235B-A22B-Instruct-2507"]


def test_normalize_model_name_strips_whitespace():
    assert _normalize_model_name(" Qwen3-Plus ") == "Qwen3-Plus"


def test_extract_chat_content_reads_normal_response():
    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="你好")
            )
        ]
    )

    assert _extract_chat_content(response) == "你好"


def test_extract_chat_content_raises_clear_error_for_error_object():
    response = SimpleNamespace(
        choices=None,
        code=404,
        message="The model `bad-model` does not exist.",
    )

    with pytest.raises(ValueError, match="LLM API 错误\\(code=404\\): The model `bad-model` does not exist."):
        _extract_chat_content(response)
