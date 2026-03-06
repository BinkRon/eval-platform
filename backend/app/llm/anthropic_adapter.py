import json
import re

from anthropic import AsyncAnthropic

from app.llm.base import LLMAdapter


class AnthropicAdapter(LLMAdapter):
    def __init__(self, api_key: str, model: str, base_url: str | None = None,
                 timeout: float = 60.0, max_retries: int = 2):
        super().__init__(api_key, model, base_url, timeout, max_retries)
        kwargs = {"api_key": api_key, "timeout": timeout, "max_retries": max_retries}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = AsyncAnthropic(**kwargs)

    async def chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text

    async def chat_json(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        json_schema: dict | None = None,
    ) -> dict:
        prompt = system_prompt or ""
        prompt += "\n\nYou must respond with valid JSON only. No other text."

        text = await self.chat(messages, prompt, temperature, max_tokens)
        text = text.strip()
        # Try to extract from markdown code block
        code_block_match = re.search(r'```(?:json)?\s*\n(.*?)\n\s*```', text, re.DOTALL)
        if code_block_match:
            text = code_block_match.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise ValueError(f"LLM returned invalid JSON: {text[:200]}")
