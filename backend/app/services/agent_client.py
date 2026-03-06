import json
import uuid

import httpx
from jsonpath_ng import parse as jsonpath_parse

from app.models.agent_version import AgentVersion


class AgentClient:
    def __init__(self, agent_version: AgentVersion):
        self.agent = agent_version
        self.session_id = str(uuid.uuid4())

    async def send_message(self, message: str) -> tuple[str, bool]:
        """Send a message to the agent and return (reply, is_ended).

        Returns:
            tuple: (agent reply text, whether agent signaled end)
        """
        # Build request body from template
        body = self._build_request_body(message)

        headers = {}
        if self.agent.auth_type == "bearer" and self.agent.auth_token:
            headers["Authorization"] = f"Bearer {self.agent.auth_token}"
        elif self.agent.auth_type == "header" and self.agent.auth_token:
            # Format: "Header-Name: value"
            if ":" in self.agent.auth_token:
                key, val = self.agent.auth_token.split(":", 1)
                headers[key.strip()] = val.strip()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method=self.agent.method or "POST",
                url=self.agent.endpoint,
                json=body,
                headers=headers,
            )
            response.raise_for_status()

        data = response.json()

        # Extract reply using JSONPath
        reply = self._extract_value(data, self.agent.response_path) if self.agent.response_path else str(data)

        # Check end signal
        is_ended = False
        if self.agent.has_end_signal and self.agent.end_signal_path:
            signal_value = self._extract_value(data, self.agent.end_signal_path)
            expected = self.agent.end_signal_value or "true"
            is_ended = str(signal_value).lower() == expected.lower()

        return reply, is_ended

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
