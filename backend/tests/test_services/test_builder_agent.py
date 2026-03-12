"""Tests for builder_agent_service: system prompt assembly and LLM interaction."""
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.builder_agent_service import (
    BUILDER_SYSTEM_PROMPT,
    _load_project_context,
    chat,
)


class TestBuilderSystemPrompt:
    def test_system_prompt_not_empty(self):
        assert len(BUILDER_SYSTEM_PROMPT) > 100

    def test_system_prompt_contains_role(self):
        assert "构建助手" in BUILDER_SYSTEM_PROMPT

    def test_system_prompt_contains_capabilities(self):
        assert "对练测试用例" in BUILDER_SYSTEM_PROMPT
        assert "裁判配置" in BUILDER_SYSTEM_PROMPT


class TestLoadProjectContext:
    @pytest.mark.asyncio
    async def test_no_files_returns_empty(self):
        """When project has no files, context should be empty."""
        mock_db = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await _load_project_context(mock_db, uuid.uuid4())
        assert result == ""

    @pytest.mark.asyncio
    async def test_files_included_in_context(self):
        """File content should appear in context with filename header."""
        file1 = SimpleNamespace(
            filename="manual.txt",
            file_type="txt",
            storage_path="/tmp/test.txt",
        )
        mock_db = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [file1]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        with patch("app.services.builder_agent_service.parse_file", return_value="File content here"):
            result = await _load_project_context(mock_db, uuid.uuid4())

        assert "manual.txt" in result
        assert "File content here" in result

    @pytest.mark.asyncio
    async def test_empty_file_content_excluded(self):
        """Files that parse to empty string should not appear in context."""
        file1 = SimpleNamespace(
            filename="empty.pdf",
            file_type="pdf",
            storage_path="/tmp/empty.pdf",
        )
        mock_db = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [file1]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        with patch("app.services.builder_agent_service.parse_file", return_value=""):
            result = await _load_project_context(mock_db, uuid.uuid4())

        assert result == ""


class TestChat:
    @pytest.mark.asyncio
    async def test_chat_calls_llm_and_saves_messages(self, mock_llm):
        """chat() should save user message, call LLM, save assistant response."""
        project_id = uuid.uuid4()
        mock_db = AsyncMock()

        # Mock project lookup
        mock_project = SimpleNamespace(id=project_id, name="Test")
        mock_db.get.return_value = mock_project

        # Mock conversation
        mock_conv = SimpleNamespace(
            id=uuid.uuid4(),
            project_id=project_id,
            messages=[{"role": "user", "content": "帮我生成用例"}],
        )

        mock_llm.chat_responses = ["好的，我来帮你生成用例。"]

        with (
            patch("app.services.builder_agent_service.append_message", new_callable=AsyncMock) as mock_append,
            patch("app.services.builder_agent_service.get_or_create", new_callable=AsyncMock, return_value=mock_conv),
            patch("app.services.builder_agent_service._get_llm_adapter", new_callable=AsyncMock, return_value=mock_llm),
            patch("app.services.builder_agent_service._load_project_context", new_callable=AsyncMock, return_value=""),
        ):
            result = await chat(mock_db, project_id, "帮我生成用例", "openai", "gpt-4")

        assert result == "好的，我来帮你生成用例。"
        # Should have been called twice: once for user, once for assistant
        assert mock_append.call_count == 2
        # First call: user message
        assert mock_append.call_args_list[0][0][2] == "user"
        assert mock_append.call_args_list[0][0][3] == "帮我生成用例"
        # Second call: assistant response
        assert mock_append.call_args_list[1][0][2] == "assistant"

    @pytest.mark.asyncio
    async def test_chat_includes_file_context_in_system_prompt(self, mock_llm):
        """When project has files, system prompt should include file content."""
        project_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_db.get.return_value = SimpleNamespace(id=project_id, name="Test")

        mock_conv = SimpleNamespace(
            id=uuid.uuid4(), project_id=project_id,
            messages=[{"role": "user", "content": "test"}],
        )
        mock_llm.chat_responses = ["response"]

        with (
            patch("app.services.builder_agent_service.append_message", new_callable=AsyncMock),
            patch("app.services.builder_agent_service.get_or_create", new_callable=AsyncMock, return_value=mock_conv),
            patch("app.services.builder_agent_service._get_llm_adapter", new_callable=AsyncMock, return_value=mock_llm),
            patch("app.services.builder_agent_service._load_project_context", new_callable=AsyncMock, return_value="话术手册内容"),
        ):
            await chat(mock_db, project_id, "test", "openai", "gpt-4")

        # Verify system prompt passed to LLM includes file context
        call_args = mock_llm.chat_call_args[0]
        assert "话术手册内容" in call_args["system_prompt"]
        assert "项目文件内容" in call_args["system_prompt"]
