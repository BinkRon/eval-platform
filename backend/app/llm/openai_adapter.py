import json
import re

from openai import AsyncOpenAI

from app.llm.base import LLMAdapter

_THINK_RE = re.compile(r"<think>[\s\S]*?</think>\s*", re.IGNORECASE)
_CODE_BLOCK_RE = re.compile(r"^```(?:json)?\s*\n?([\s\S]*?)\n?\s*```\s*$")
_CODE_BLOCK_OPEN_RE = re.compile(r"^```(?:json)?\s*\n?([\s\S]*)")  # unclosed block


def _extract_json_content(content: str) -> str:
    """Extract JSON from LLM output that may be wrapped in markdown code blocks.

    Handles: raw JSON, ```json...```, unclosed ```json... (truncated output),
    and JSON embedded in surrounding text.
    """
    # 1. Closed code block: ```json ... ```
    m = _CODE_BLOCK_RE.match(content)
    if m:
        return m.group(1).strip()

    # 2. Unclosed code block (truncated output): ```json ...
    m = _CODE_BLOCK_OPEN_RE.match(content)
    if m:
        return m.group(1).strip()

    # 3. JSON embedded in text — find outermost { ... }
    start = content.find("{")
    if start != -1:
        end = content.rfind("}")
        if end > start:
            return content[start:end + 1]

    return content


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
        content = response.choices[0].message.content or ""
        return _THINK_RE.sub("", content).strip()

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
        content = _THINK_RE.sub("", content).strip()
        content = _extract_json_content(content)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"LLM returned invalid JSON: {content[:200]}")
