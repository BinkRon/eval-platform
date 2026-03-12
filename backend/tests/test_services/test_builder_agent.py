"""Tests for builder_agent_service: system prompt, config parsing, config application."""
import json
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.builder_agent_service import (
    BUILDER_SYSTEM_PROMPT,
    _load_project_context,
    apply_generated_config,
    build_card_data,
    chat,
    parse_config_block,
)


# ---------------------------------------------------------------------------
# System Prompt tests
# ---------------------------------------------------------------------------


class TestBuilderSystemPrompt:
    def test_system_prompt_not_empty(self):
        assert len(BUILDER_SYSTEM_PROMPT) > 100

    def test_system_prompt_contains_role(self):
        assert "构建助手" in BUILDER_SYSTEM_PROMPT

    def test_system_prompt_contains_skills(self):
        assert "Skill 一" in BUILDER_SYSTEM_PROMPT
        assert "Skill 二" in BUILDER_SYSTEM_PROMPT
        assert "对练用例生成" in BUILDER_SYSTEM_PROMPT
        assert "裁判配置生成" in BUILDER_SYSTEM_PROMPT

    def test_system_prompt_contains_output_format(self):
        assert "<generated_config>" in BUILDER_SYSTEM_PROMPT
        assert "config_type" in BUILDER_SYSTEM_PROMPT

    def test_system_prompt_contains_test_case_fields(self):
        assert "sparring_prompt" in BUILDER_SYSTEM_PROMPT
        assert "first_message" in BUILDER_SYSTEM_PROMPT

    def test_system_prompt_contains_judge_config_fields(self):
        assert "checklist_items" in BUILDER_SYSTEM_PROMPT
        assert "eval_dimensions" in BUILDER_SYSTEM_PROMPT
        assert "judge_prompt_segment" in BUILDER_SYSTEM_PROMPT
        assert "pass_threshold" in BUILDER_SYSTEM_PROMPT

    def test_system_prompt_contains_quality_guidelines(self):
        assert "多样性" in BUILDER_SYSTEM_PROMPT
        assert "压力测试" in BUILDER_SYSTEM_PROMPT
        assert "评分锚点" in BUILDER_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Config block parsing tests
# ---------------------------------------------------------------------------


class TestParseConfigBlock:
    def test_no_config_block(self):
        """Plain text returns as-is with no config."""
        msg, config = parse_config_block("这是一段普通对话。")
        assert msg == "这是一段普通对话。"
        assert config is None

    def test_valid_test_cases_block(self):
        """Valid test_cases config block is extracted correctly."""
        config_json = json.dumps({
            "config_type": "test_cases",
            "test_cases": [
                {"name": "用例1", "sparring_prompt": "角色描述", "first_message": "喂？"}
            ],
        }, ensure_ascii=False)
        raw = f"我帮你生成了用例：\n<generated_config>\n{config_json}\n</generated_config>\n请确认。"

        msg, config = parse_config_block(raw)
        assert "我帮你生成了用例" in msg
        assert "请确认" in msg
        assert "<generated_config>" not in msg
        assert config is not None
        assert config["config_type"] == "test_cases"
        assert len(config["test_cases"]) == 1

    def test_valid_judge_config_block(self):
        """Valid judge_config block is extracted correctly."""
        config_json = json.dumps({
            "config_type": "judge_config",
            "checklist_items": [{"content": "是否问候", "level": "required"}],
            "eval_dimensions": [{"name": "专业性", "judge_prompt_segment": "评判指引"}],
            "pass_threshold": 2.0,
        }, ensure_ascii=False)
        raw = f"裁判配置如下：\n<generated_config>\n{config_json}\n</generated_config>"

        msg, config = parse_config_block(raw)
        assert config is not None
        assert config["config_type"] == "judge_config"
        assert len(config["checklist_items"]) == 1
        assert len(config["eval_dimensions"]) == 1

    def test_invalid_json_returns_none(self):
        """Malformed JSON returns original message with None config."""
        raw = "结果：\n<generated_config>\n{invalid json}\n</generated_config>"
        msg, config = parse_config_block(raw)
        assert msg == raw
        assert config is None

    def test_missing_config_type_returns_none(self):
        """JSON without config_type field returns None."""
        config_json = json.dumps({"test_cases": []})
        raw = f"<generated_config>\n{config_json}\n</generated_config>"
        msg, config = parse_config_block(raw)
        assert config is None

    def test_unknown_config_type_returns_none(self):
        """Unknown config_type returns None."""
        config_json = json.dumps({"config_type": "unknown_type"})
        raw = f"<generated_config>\n{config_json}\n</generated_config>"
        msg, config = parse_config_block(raw)
        assert config is None

    def test_multiline_sparring_prompt(self):
        """Config with multiline prompts using \\n escapes is parsed correctly."""
        config_json = json.dumps({
            "config_type": "test_cases",
            "test_cases": [{
                "name": "退休客户",
                "sparring_prompt": "## 角色身份\n58岁退休员工\n\n## 行为规则\n- 谨慎\n- 不信任",
            }],
        }, ensure_ascii=False)
        raw = f"<generated_config>\n{config_json}\n</generated_config>"
        msg, config = parse_config_block(raw)
        assert config is not None
        assert "58岁退休员工" in config["test_cases"][0]["sparring_prompt"]


# ---------------------------------------------------------------------------
# Card data building tests
# ---------------------------------------------------------------------------


class TestBuildCardData:
    @pytest.mark.asyncio
    async def test_test_cases_card_data(self):
        """Test cases card data includes items and impact message."""
        mock_db = AsyncMock()
        # Mock count query
        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        mock_db.execute.return_value = mock_result

        config_data = {
            "config_type": "test_cases",
            "test_cases": [
                {"name": "用例A", "sparring_prompt": "角色描述A"},
                {"name": "用例B", "sparring_prompt": "角色描述B"},
            ],
        }
        card_type, card_data = await build_card_data(mock_db, uuid.uuid4(), config_data)
        assert card_type == "generate_confirm"
        assert "2 条" in card_data["title"]
        assert len(card_data["items"]) == 2
        assert card_data["existing_count"] == 3
        assert "3 条用例" in card_data["impact_message"]
        assert card_data["config_payload"] == config_data

    @pytest.mark.asyncio
    async def test_judge_config_card_data(self):
        """Judge config card data includes checklist and dimension items."""
        mock_db = AsyncMock()
        # Mock judge config query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        config_data = {
            "config_type": "judge_config",
            "checklist_items": [
                {"content": "检查项1", "level": "required"},
            ],
            "eval_dimensions": [
                {"name": "专业性", "judge_prompt_segment": "评判指引"},
            ],
            "pass_threshold": 2.0,
        }
        card_type, card_data = await build_card_data(mock_db, uuid.uuid4(), config_data)
        assert card_type == "generate_confirm"
        assert "1 检查项" in card_data["title"]
        assert "1 维度" in card_data["title"]
        assert card_data["existing_count"] == 0


# ---------------------------------------------------------------------------
# Load project context tests
# ---------------------------------------------------------------------------


class TestLoadProjectContext:
    @pytest.mark.asyncio
    async def test_no_files_returns_empty(self):
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
        file1 = SimpleNamespace(
            filename="manual.txt", file_type="txt", storage_path="/tmp/test.txt",
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


# ---------------------------------------------------------------------------
# Chat integration tests
# ---------------------------------------------------------------------------


class TestChat:
    @pytest.mark.asyncio
    async def test_plain_text_response(self, mock_llm):
        """Plain text response returns dict with no card."""
        project_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_db.get.return_value = SimpleNamespace(id=project_id, name="Test")

        mock_conv = SimpleNamespace(
            id=uuid.uuid4(), project_id=project_id,
            messages=[],
        )
        mock_llm.chat_responses = ["好的，请告诉我你的业务场景。"]

        with (
            patch("app.services.builder_agent_service.append_message", new_callable=AsyncMock),
            patch("app.services.builder_agent_service.get_or_create", new_callable=AsyncMock, return_value=mock_conv),
            patch("app.services.builder_agent_service._get_llm_adapter", new_callable=AsyncMock, return_value=mock_llm),
            patch("app.services.builder_agent_service._load_project_context", new_callable=AsyncMock, return_value=""),
        ):
            result = await chat(mock_db, project_id, "帮我生成用例", "openai", "gpt-4")

        assert isinstance(result, dict)
        assert result["response"] == "好的，请告诉我你的业务场景。"
        assert result["card_type"] is None
        assert result["card_data"] is None

    @pytest.mark.asyncio
    async def test_response_with_config_block(self, mock_llm):
        """Response with config block returns generate_confirm card."""
        project_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_db.get.return_value = SimpleNamespace(id=project_id, name="Test")

        mock_conv = SimpleNamespace(
            id=uuid.uuid4(), project_id=project_id, messages=[],
        )

        config_json = json.dumps({
            "config_type": "test_cases",
            "test_cases": [
                {"name": "退休客户", "sparring_prompt": "58岁退休"},
            ],
        }, ensure_ascii=False)
        mock_llm.chat_responses = [
            f"我为你生成了1条用例：\n<generated_config>\n{config_json}\n</generated_config>"
        ]

        # Mock count query for build_card_data
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        # Setup mock_db.execute to return count result for the card data query
        original_execute = mock_db.execute

        async def custom_execute(stmt, *args, **kwargs):
            return mock_count_result
        mock_db.execute = AsyncMock(side_effect=custom_execute)

        with (
            patch("app.services.builder_agent_service.append_message", new_callable=AsyncMock),
            patch("app.services.builder_agent_service.get_or_create", new_callable=AsyncMock, return_value=mock_conv),
            patch("app.services.builder_agent_service._get_llm_adapter", new_callable=AsyncMock, return_value=mock_llm),
            patch("app.services.builder_agent_service._load_project_context", new_callable=AsyncMock, return_value=""),
        ):
            result = await chat(mock_db, project_id, "生成用例", "openai", "gpt-4")

        assert result["card_type"] == "generate_confirm"
        assert result["card_data"] is not None
        assert result["card_data"]["config_type"] == "test_cases"
        assert "退休客户" in result["card_data"]["items"][0]["name"]
        assert "<generated_config>" not in result["response"]

    @pytest.mark.asyncio
    async def test_chat_saves_raw_response(self, mock_llm):
        """Chat saves the raw response (with config block) to conversation history."""
        project_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_db.get.return_value = SimpleNamespace(id=project_id, name="Test")

        mock_conv = SimpleNamespace(
            id=uuid.uuid4(), project_id=project_id, messages=[],
        )

        raw_response = "文本\n<generated_config>\n{\"config_type\":\"test_cases\",\"test_cases\":[]}\n</generated_config>"
        mock_llm.chat_responses = [raw_response]

        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_db.execute = AsyncMock(return_value=mock_count)

        with (
            patch("app.services.builder_agent_service.append_message", new_callable=AsyncMock) as mock_append,
            patch("app.services.builder_agent_service.get_or_create", new_callable=AsyncMock, return_value=mock_conv),
            patch("app.services.builder_agent_service._get_llm_adapter", new_callable=AsyncMock, return_value=mock_llm),
            patch("app.services.builder_agent_service._load_project_context", new_callable=AsyncMock, return_value=""),
        ):
            await chat(mock_db, project_id, "test", "openai", "gpt-4")

        # Verify raw response (with config block) was saved
        assistant_content = mock_append.call_args_list[1][0][3]
        assert "<generated_config>" in assistant_content

    @pytest.mark.asyncio
    async def test_chat_includes_file_context_in_system_prompt(self, mock_llm):
        """When project has files, system prompt should include file content."""
        project_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_db.get.return_value = SimpleNamespace(id=project_id, name="Test")
        mock_conv = SimpleNamespace(
            id=uuid.uuid4(), project_id=project_id, messages=[],
        )
        mock_llm.chat_responses = ["response"]

        with (
            patch("app.services.builder_agent_service.append_message", new_callable=AsyncMock),
            patch("app.services.builder_agent_service.get_or_create", new_callable=AsyncMock, return_value=mock_conv),
            patch("app.services.builder_agent_service._get_llm_adapter", new_callable=AsyncMock, return_value=mock_llm),
            patch("app.services.builder_agent_service._load_project_context", new_callable=AsyncMock, return_value="话术手册内容"),
        ):
            await chat(mock_db, project_id, "test", "openai", "gpt-4")

        call_args = mock_llm.chat_call_args[0]
        assert "话术手册内容" in call_args["system_prompt"]

    @pytest.mark.asyncio
    async def test_chat_json_retry_on_parse_failure(self, mock_llm):
        """When config block has invalid JSON, retry with chat_json."""
        project_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_db.get.return_value = SimpleNamespace(id=project_id, name="Test")
        mock_conv = SimpleNamespace(
            id=uuid.uuid4(), project_id=project_id, messages=[],
        )

        # First response has broken JSON in config block
        mock_llm.chat_responses = [
            "生成结果：\n<generated_config>\n{broken json}\n</generated_config>"
        ]
        # Retry with chat_json returns valid config
        mock_llm.chat_json_responses = [{
            "config_type": "test_cases",
            "test_cases": [{"name": "用例1", "sparring_prompt": "描述"}],
        }]

        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_db.execute = AsyncMock(return_value=mock_count)

        with (
            patch("app.services.builder_agent_service.append_message", new_callable=AsyncMock),
            patch("app.services.builder_agent_service.get_or_create", new_callable=AsyncMock, return_value=mock_conv),
            patch("app.services.builder_agent_service._get_llm_adapter", new_callable=AsyncMock, return_value=mock_llm),
            patch("app.services.builder_agent_service._load_project_context", new_callable=AsyncMock, return_value=""),
        ):
            result = await chat(mock_db, project_id, "生成", "openai", "gpt-4")

        assert result["card_type"] == "generate_confirm"
        assert mock_llm.chat_json_call_count == 1


# ---------------------------------------------------------------------------
# Apply config tests
# ---------------------------------------------------------------------------


class TestApplyTestCases:
    @pytest.mark.asyncio
    async def test_append_test_cases(self):
        """Append mode creates test cases via db.add with offset sort_order."""
        project_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_db.get.return_value = SimpleNamespace(id=project_id, name="Test")

        # Mock: max sort_order = 2
        mock_max_result = MagicMock()
        mock_max_result.scalar.return_value = 2
        mock_db.execute = AsyncMock(return_value=mock_max_result)

        # Track db.add calls
        added_objects = []
        mock_db.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

        config_payload = {
            "config_type": "test_cases",
            "test_cases": [
                {"name": "用例A", "sparring_prompt": "描述A"},
                {"name": "用例B", "sparring_prompt": "描述B", "first_message": "你好"},
            ],
        }

        result = await apply_generated_config(
            mock_db, project_id, "test_cases", config_payload, "append"
        )

        assert result["created"] == 2
        assert result["mode"] == "append"
        assert len(added_objects) == 2
        # Check sort_order offset: 2 + 1 = 3, so first is 3, second is 4
        assert added_objects[0].sort_order == 3
        assert added_objects[1].sort_order == 4
        assert added_objects[1].first_message == "你好"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_replace_test_cases(self):
        """Replace mode deletes existing then creates new, all in one commit."""
        project_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_db.get.return_value = SimpleNamespace(id=project_id, name="Test")

        # Mock existing test cases
        existing_tc = SimpleNamespace(id=uuid.uuid4())
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [existing_tc]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        added_objects = []
        mock_db.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

        config_payload = {
            "config_type": "test_cases",
            "test_cases": [{"name": "新用例", "sparring_prompt": "新描述"}],
        }

        result = await apply_generated_config(
            mock_db, project_id, "test_cases", config_payload, "replace"
        )

        assert result["created"] == 1
        assert result["mode"] == "replace"
        mock_db.delete.assert_called_once_with(existing_tc)
        assert len(added_objects) == 1
        assert added_objects[0].sort_order == 0
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_test_cases_raises(self):
        """Empty test_cases list raises ValidationError."""
        project_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_db.get.return_value = SimpleNamespace(id=project_id, name="Test")

        with pytest.raises(Exception, match="没有可写入的测试用例"):
            await apply_generated_config(
                mock_db, project_id, "test_cases",
                {"config_type": "test_cases", "test_cases": []}, "append"
            )


class TestApplyJudgeConfig:
    @pytest.mark.asyncio
    async def test_replace_judge_config(self):
        """Replace mode creates fresh judge config."""
        project_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_db.get.return_value = SimpleNamespace(id=project_id, name="Test")

        config_payload = {
            "config_type": "judge_config",
            "checklist_items": [
                {"content": "是否问候", "level": "required"},
                {"content": "是否解决", "level": "important"},
            ],
            "eval_dimensions": [
                {"name": "专业性", "judge_prompt_segment": "评判指引"},
            ],
            "pass_threshold": 2.5,
        }

        with patch(
            "app.services.judge_config_service.save_judge_config",
            new_callable=AsyncMock,
        ) as mock_save:
            result = await apply_generated_config(
                mock_db, project_id, "judge_config", config_payload, "replace"
            )

        assert result["checklist_count"] == 2
        assert result["dimension_count"] == 1
        assert result["mode"] == "replace"
        # Verify save was called with correct data
        save_call = mock_save.call_args[0]
        update_data = save_call[2]
        assert update_data.pass_threshold == 2.5
        assert len(update_data.checklist_items) == 2
        assert len(update_data.eval_dimensions) == 1
        # Verify level mapping: required→must, important→should
        assert update_data.checklist_items[0].level == "must"
        assert update_data.checklist_items[1].level == "should"
        # Verify commit was called after save
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_level_falls_back_to_should(self):
        """Unknown level values from LLM (e.g. 'critical') fall back to 'should'."""
        project_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_db.get.return_value = SimpleNamespace(id=project_id, name="Test")

        config_payload = {
            "config_type": "judge_config",
            "checklist_items": [
                {"content": "检查项", "level": "critical"},  # unknown level
            ],
            "eval_dimensions": [],
            "pass_threshold": 2.0,
        }

        with patch(
            "app.services.judge_config_service.save_judge_config",
            new_callable=AsyncMock,
        ) as mock_save:
            await apply_generated_config(
                mock_db, project_id, "judge_config", config_payload, "replace"
            )

        save_call = mock_save.call_args[0]
        update_data = save_call[2]
        assert update_data.checklist_items[0].level == "should"

    @pytest.mark.asyncio
    async def test_append_judge_config(self):
        """Append mode merges with existing config."""
        project_id = uuid.uuid4()
        mock_db = AsyncMock()
        mock_db.get.return_value = SimpleNamespace(id=project_id, name="Test")

        # Mock existing judge config
        existing_config = SimpleNamespace(
            pass_threshold=2.0,
            checklist_items=[
                SimpleNamespace(content="旧检查项", level="must", sort_order=0),
            ],
            eval_dimensions=[
                SimpleNamespace(name="旧维度", judge_prompt_segment="旧指引", sort_order=0),
            ],
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_config
        mock_db.execute = AsyncMock(return_value=mock_result)

        config_payload = {
            "config_type": "judge_config",
            "checklist_items": [{"content": "新检查项", "level": "important"}],
            "eval_dimensions": [{"name": "新维度", "judge_prompt_segment": "新指引"}],
            "pass_threshold": 2.5,  # This should be ignored in append mode
        }

        with patch(
            "app.services.judge_config_service.save_judge_config",
            new_callable=AsyncMock,
        ) as mock_save:
            result = await apply_generated_config(
                mock_db, project_id, "judge_config", config_payload, "append"
            )

        assert result["checklist_count"] == 1
        assert result["dimension_count"] == 1
        assert result["mode"] == "append"
        # Verify merged data
        save_call = mock_save.call_args[0]
        update_data = save_call[2]
        assert update_data.pass_threshold == 2.0  # Existing threshold preserved
        assert len(update_data.checklist_items) == 2  # 1 old + 1 new
        assert len(update_data.eval_dimensions) == 2  # 1 old + 1 new
        # Verify commit was called after save
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_config_type_raises(self):
        """Unknown config_type raises ValidationError."""
        mock_db = AsyncMock()
        mock_db.get.return_value = SimpleNamespace(id=uuid.uuid4(), name="Test")

        with pytest.raises(Exception, match="不支持的配置类型"):
            await apply_generated_config(
                mock_db, uuid.uuid4(), "unknown_type", {}, "append"
            )
