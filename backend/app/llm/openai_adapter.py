import json

from openai import AsyncOpenAI

from app.llm.base import LLMAdapter


class OpenAIAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: str, base_url: str | None = None,
                 timeout: float = 60.0, max_retries: int = 2):
        super().__init__(api_key, model, base_url, timeout, max_retries)
        kwargs = {"api_key": api_key, "timeout": timeout, "max_retries": max_retries}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = AsyncOpenAI(**kwargs)

    async def chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def chat_json(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        json_schema: dict | None = None,
    ) -> dict:
        msgs = []
        prompt = system_prompt or ""
        prompt += "\n\nYou must respond with valid JSON only."
        msgs.append({"role": "system", "content": prompt})
        msgs.extend(messages)

        kwargs = {
            "model": self.model,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        response = await self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"LLM returned invalid JSON: {content[:200]}")
