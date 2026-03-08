from app.llm.anthropic_adapter import AnthropicAdapter
from app.llm.base import LLMAdapter
from app.llm.openai_adapter import OpenAIAdapter

_ADAPTERS: dict[str, type[LLMAdapter]] = {
    "anthropic": AnthropicAdapter,
    "openai": OpenAIAdapter,
    "dashscope": OpenAIAdapter,
}


def create_llm_adapter(
    provider_name: str,
    api_key: str,
    model: str,
    base_url: str | None = None,
) -> LLMAdapter:
    adapter_cls = _ADAPTERS.get(provider_name)
    if not adapter_cls:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(_ADAPTERS.keys())}")
    return adapter_cls(api_key=api_key, model=model, base_url=base_url)
