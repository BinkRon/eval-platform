import ipaddress
import json
import logging
import socket
import uuid
from urllib.parse import urlparse

import httpx
from jsonpath_ng import parse as jsonpath_parse

from app.models.agent_version import AgentVersion

logger = logging.getLogger(__name__)


def _validate_url(url: str) -> None:
    """Validate URL to prevent SSRF attacks.

    Note: DNS rebinding is not fully mitigated — the IP check and actual
    HTTP request are not atomic. Acceptable for MVP.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"不支持的 URL 协议: {parsed.scheme}，仅允许 http/https")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL 缺少主机名")

    if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("不允许访问本地地址")

    try:
        addrinfos = socket.getaddrinfo(hostname, None)
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

    async def send_message(self, message: str) -> tuple[str, bool]:
        """Send a message to the agent and return (reply, is_ended).

        Returns:
            tuple: (agent reply text, whether agent signaled end)
        """
        _validate_url(self.agent.endpoint)
        if self.agent.response_format == "sse":
            return await self._send_message_sse(message)
        return await self._send_message_json(message)

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
            raise RuntimeError(f"Agent API 连接失败: {self.agent.endpoint}")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Agent API 返回错误状态码 {e.response.status_code}")
        except httpx.HTTPError as e:
            raise RuntimeError(f"Agent API 网络错误: {e}")

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

        try:
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

                        last_event_data = event_data

                        # Extract text chunk using response_path
                        if self.agent.response_path:
                            try:
                                chunk_text = self._extract_value(event_data, self.agent.response_path)
                                if chunk_text:
                                    chunks.append(str(chunk_text))
                            except ValueError:
                                pass  # Path not found in this event, skip
        except httpx.TimeoutException:
            raise RuntimeError("Agent API 调用超时（SSE 流式）")
        except httpx.ConnectError:
            raise RuntimeError(f"Agent API 连接失败: {self.agent.endpoint}")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Agent API 返回错误状态码 {e.response.status_code}")
        except httpx.HTTPError as e:
            raise RuntimeError(f"Agent API 网络错误: {e}")

        if not chunks:
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
        return self._replace_placeholders(body, placeholders)

    @staticmethod
    def _replace_placeholders(obj, placeholders: dict):
        if isinstance(obj, str):
            for key, value in placeholders.items():
                obj = obj.replace(key, value)
            return obj
        elif isinstance(obj, dict):
            return {k: AgentClient._replace_placeholders(v, placeholders) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [AgentClient._replace_placeholders(item, placeholders) for item in obj]
        return obj

    @staticmethod
    def _extract_value(data: dict, path: str):
        expr = jsonpath_parse(path)
        matches = expr.find(data)
        if not matches:
            raise ValueError(f"JSONPath '{path}' not found in response")
        return matches[0].value
