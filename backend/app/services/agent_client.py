import asyncio
import ipaddress
import json
import logging
import socket
import uuid
from urllib.parse import urlparse

import httpx
from jsonpath_ng import parse as jsonpath_parse

from app.config import settings
from app.models.agent_version import AgentVersion

logger = logging.getLogger(__name__)


async def _validate_url(url: str) -> None:
    """Validate URL to prevent SSRF attacks.

    Set env ALLOW_PRIVATE_URLS=true to allow internal network addresses
    (for development / internal agent testing).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"不支持的 URL 协议: {parsed.scheme}，仅允许 http/https")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL 缺少主机名")

    if settings.allow_private_urls:
        return

    if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("不允许访问本地地址")

    try:
        loop = asyncio.get_running_loop()
        addrinfos = await loop.run_in_executor(None, socket.getaddrinfo, hostname, None)
    except socket.gaierror:
        raise ValueError(f"无法解析主机名: {hostname}")

    for family, _, _, _, sockaddr in addrinfos:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError("不允许访问内部网络地址")


class AgentClient:
    def __init__(self, agent_version: AgentVersion):
        self.agent = agent_version
        self.session_id = str(uuid.uuid4())
        self._history: list[dict] = []

    async def send_message(self, message: str) -> tuple[str, bool]:
        """Send a message to the agent and return (reply, is_ended).

        Returns:
            tuple: (agent reply text, whether agent signaled end)
        """
        await _validate_url(self.agent.endpoint)
        if self.agent.response_format == "sse":
            reply, ended = await self._send_message_sse(message)
        else:
            reply, ended = await self._send_message_json(message)
        # Track conversation history for {{dialog_history}} placeholder
        self._history.append({"role": "user", "content": message})
        self._history.append({"role": "assistant", "content": reply})
        return reply, ended

    async def _send_message_json(self, message: str) -> tuple[str, bool]:
        body = self._build_request_body(message)
        headers = self._build_headers()

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.request(
                    method=self.agent.method or "POST",
                    url=self.agent.endpoint,
                    json=body,
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.TimeoutException:
            raise RuntimeError("Agent API 调用超时")
        except httpx.ConnectError:
            raise RuntimeError("Agent API 连接失败")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Agent API 返回错误状态码 {e.response.status_code}")
        except httpx.HTTPError:
            raise RuntimeError("Agent API 网络错误")

        try:
            data = response.json()
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise RuntimeError("Agent API 返回非 JSON 响应")

        reply = self._extract_value(data, self.agent.response_path) if self.agent.response_path else str(data)
        is_ended = self._check_end_signal(data)
        return reply, is_ended

    async def _send_message_sse(self, message: str) -> tuple[str, bool]:
        """Handle SSE (Server-Sent Events) streaming response.

        Reads all `data:` events, extracts text from each using response_path,
        concatenates them into the full reply. Uses the last event for end signal.
        """
        body = self._build_request_body(message)
        headers = self._build_headers()

        # SSE streams need longer read timeout
        timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)

        chunks: list[str] = []
        last_event_data: dict | None = None
        event_count = 0

        try:
            async with asyncio.timeout(300):
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream(
                        method=self.agent.method or "POST",
                        url=self.agent.endpoint,
                        json=body,
                        headers=headers,
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            line = line.strip()
                            if not line or not line.startswith("data:"):
                                continue

                            payload = line[len("data:"):].strip()
                            if payload == "[DONE]":
                                break

                            try:
                                event_data = json.loads(payload)
                            except json.JSONDecodeError:
                                logger.warning(f"SSE 事件 JSON 解析失败: {payload[:100]}")
                                continue

                            event_count += 1
                            last_event_data = event_data

                            # Extract text chunk using response_path
                            if self.agent.response_path:
                                try:
                                    chunk_text = self._extract_value(event_data, self.agent.response_path)
                                    if chunk_text:
                                        chunks.append(str(chunk_text))
                                except ValueError:
                                    pass  # Path not found in this event, skip
        except TimeoutError:
            raise RuntimeError("Agent API SSE 流式响应总超时")
        except httpx.TimeoutException:
            raise RuntimeError("Agent API 调用超时（SSE 流式）")
        except httpx.ConnectError:
            raise RuntimeError("Agent API 连接失败")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Agent API 返回错误状态码 {e.response.status_code}")
        except httpx.HTTPError:
            raise RuntimeError("Agent API 网络错误")

        if not chunks:
            # Agent may send end signal with empty text (e.g. hangup with no reply).
            # This is valid — treat as empty reply + ended.
            if last_event_data and self._check_end_signal(last_event_data):
                logger.info(
                    f"SSE 流无文本但检测到结束信号: event_count={event_count}, "
                    f"session={self.session_id}"
                )
                return "", True

            logger.error(
                f"SSE 流未提取到文本: event_count={event_count}, "
                f"session={self.session_id}, message={message[:50]!r}, "
                f"last_event_keys={list(last_event_data.keys()) if last_event_data else None}, "
                f"last_event_sample={json.dumps(last_event_data, ensure_ascii=False)[:300] if last_event_data else None}"
            )
            raise RuntimeError("Agent API SSE 流未返回有效数据")

        reply = "".join(chunks)
        is_ended = self._check_end_signal(last_event_data) if last_event_data else False
        return reply, is_ended

    def _build_headers(self) -> dict:
        headers = {}
        if self.agent.auth_type == "bearer" and self.agent.auth_token:
            headers["Authorization"] = f"Bearer {self.agent.auth_token}"
        elif self.agent.auth_type == "header" and self.agent.auth_token:
            if ":" in self.agent.auth_token:
                key, val = self.agent.auth_token.split(":", 1)
                headers[key.strip()] = val.strip()
        return headers

    def _check_end_signal(self, data: dict) -> bool:
        if self.agent.has_end_signal and self.agent.end_signal_path:
            try:
                signal_value = self._extract_value(data, self.agent.end_signal_path)
                expected = self.agent.end_signal_value or "true"
                return str(signal_value).lower() == expected.lower()
            except ValueError:
                return False
        return False

    def _build_request_body(self, message: str) -> dict:
        if not self.agent.request_template:
            return {"message": message, "session_id": self.session_id}

        try:
            body = json.loads(self.agent.request_template)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid request_template JSON: {e}")

        placeholders = {"{{message}}": message, "{{session_id}}": self.session_id}
        # Support {{dialog_history}} — replaced with actual conversation array
        typed_placeholders = {"{{dialog_history}}": self._history}
        return self._replace_placeholders(body, placeholders, typed_placeholders)

    @staticmethod
    def _replace_placeholders(obj, placeholders: dict, typed_placeholders: dict | None = None):
        if isinstance(obj, str):
            # Typed placeholders: when the entire value is a placeholder, replace with actual type
            if typed_placeholders:
                stripped = obj.strip()
                if stripped in typed_placeholders:
                    return typed_placeholders[stripped]
            for key, value in placeholders.items():
                obj = obj.replace(key, value)
            return obj
        elif isinstance(obj, dict):
            return {k: AgentClient._replace_placeholders(v, placeholders, typed_placeholders) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [AgentClient._replace_placeholders(item, placeholders, typed_placeholders) for item in obj]
        return obj

    @staticmethod
    def _extract_value(data: dict, path: str):
        expr = jsonpath_parse(path)
        matches = expr.find(data)
        if not matches:
            raise ValueError(f"JSONPath '{path}' not found in response")
        return matches[0].value
