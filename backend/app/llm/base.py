from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    def __init__(self, api_key: str, model: str, base_url: str | None = None,
                 timeout: float = 60.0, max_retries: int = 2):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        ...

    @abstractmethod
    async def chat_json(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        json_schema: dict | None = None,
    ) -> dict:
        ...
