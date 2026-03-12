"""Tests for SparringRunner: prompt building, termination conditions, and conversation flow."""
from unittest.mock import AsyncMock

import pytest

from app.services.sparring_runner import SparringRunner, END_MARKER


# ---------------------------------------------------------------------------
# TestPromptBuilding
# ---------------------------------------------------------------------------


class TestPromptBuilding:
    """Verify _build_persona_prompt assembles the correct prompt text."""

    def test_sparring_prompt_injected_directly(self, mock_llm, test_case_factory):
        """sparring_prompt should appear directly in persona prompt without splitting."""
        test_case = test_case_factory(
            sparring_prompt="## 角色\n一个急性子的老客户\n\n## 行为\n说话简短，容易发火",
            first_message="你好",
        )
        runner = SparringRunner(
            agent_client=AsyncMock(), llm=mock_llm, test_case=test_case,
            system_prompt="System prompt here",
        )
        prompt = runner.persona_prompt
        assert "System prompt here" in prompt
        assert "一个急性子的老客户" in prompt
        assert "说话简短，容易发火" in prompt
        assert "首轮发言：你好" in prompt
        assert END_MARKER in prompt

    def test_first_message_none_shows_default_in_prompt(self, mock_llm, test_case_factory):
        """When first_message is None, prompt should show default '喂？'."""
        test_case = test_case_factory(first_message=None)
        runner = SparringRunner(
            agent_client=AsyncMock(), llm=mock_llm, test_case=test_case,
            system_prompt="SP",
        )
        assert "首轮发言：喂？" in runner.persona_prompt


# ---------------------------------------------------------------------------
# TestSparringTermination
# ---------------------------------------------------------------------------


class TestSparringTermination:
    """Verify the three termination conditions: max_rounds, agent_hangup, sparring_end."""

    @pytest.mark.asyncio
    async def test_max_rounds(self, mock_llm, test_case_factory):
        test_case = test_case_factory(max_rounds=3)

        agent_client = AsyncMock()
        agent_client.send_message = AsyncMock(
            side_effect=[
                ("Agent reply 1", False),
                ("Agent reply 2", False),
                ("Agent reply 3", False),
            ]
        )

        # LLM generates next user messages (only needed for rounds 1 and 2;
        # round 3 hits max_rounds before needing a next message)
        mock_llm.chat_responses = [
            "Follow-up question 1",
            "Follow-up question 2",
        ]

        runner = SparringRunner(
            agent_client=agent_client,
            llm=mock_llm,
            test_case=test_case,
            system_prompt="You are a sparring bot.",
        )

        conversation, reason, rounds = await runner.run()

        assert reason == "max_rounds"
        assert rounds == 3
        assert agent_client.send_message.call_count == 3

    @pytest.mark.asyncio
    async def test_agent_hangup(self, mock_llm, test_case_factory):
        test_case = test_case_factory(max_rounds=10)

        agent_client = AsyncMock()
        agent_client.send_message = AsyncMock(
            side_effect=[
                ("Agent reply 1", False),
                ("Goodbye! Session ended.", True),  # Agent signals end on round 2
            ]
        )

        mock_llm.chat_responses = ["Follow-up question"]

        runner = SparringRunner(
            agent_client=agent_client,
            llm=mock_llm,
            test_case=test_case,
            system_prompt="You are a sparring bot.",
        )

        conversation, reason, rounds = await runner.run()

        assert reason == "agent_hangup"
        assert rounds == 2
        assert agent_client.send_message.call_count == 2

    @pytest.mark.asyncio
    async def test_sparring_end(self, mock_llm, test_case_factory):
        test_case = test_case_factory(max_rounds=10)

        agent_client = AsyncMock()
        agent_client.send_message = AsyncMock(
            side_effect=[
                ("Agent reply 1", False),
                ("Agent reply 2", False),
            ]
        )

        # First LLM response is normal, second contains END marker
        mock_llm.chat_responses = [
            "Normal follow-up",
            f"Thank you for your help! {END_MARKER}",
        ]

        runner = SparringRunner(
            agent_client=agent_client,
            llm=mock_llm,
            test_case=test_case,
            system_prompt="You are a sparring bot.",
        )

        conversation, reason, rounds = await runner.run()

        assert reason == "sparring_end"
        assert rounds == 2


# ---------------------------------------------------------------------------
# TestConversationFlow
# ---------------------------------------------------------------------------


class TestConversationFlow:
    """Verify conversation structure and message ordering."""

    @pytest.mark.asyncio
    async def test_message_order(self, mock_llm, test_case_factory):
        test_case = test_case_factory(
            first_message="Hi there!",
            max_rounds=2,
        )

        agent_client = AsyncMock()
        agent_client.send_message = AsyncMock(
            side_effect=[
                ("Agent says hi", False),
                ("Agent says bye", False),
            ]
        )

        mock_llm.chat_responses = ["User follow-up"]

        runner = SparringRunner(
            agent_client=agent_client,
            llm=mock_llm,
            test_case=test_case,
            system_prompt="Sparring prompt",
        )

        conversation, reason, rounds = await runner.run()

        # First message is from the user (first_message)
        assert conversation[0]["role"] == "user"
        assert conversation[0]["content"] == "Hi there!"

        # Then alternating: assistant, user, assistant
        assert conversation[1]["role"] == "assistant"
        assert conversation[1]["content"] == "Agent says hi"
        assert conversation[2]["role"] == "user"
        assert conversation[2]["content"] == "User follow-up"
        assert conversation[3]["role"] == "assistant"
        assert conversation[3]["content"] == "Agent says bye"

    @pytest.mark.asyncio
    async def test_first_message_none_fallback(self, mock_llm, test_case_factory):
        """When first_message is None, should fall back to '喂？'."""
        test_case = test_case_factory(first_message=None, max_rounds=1)

        agent_client = AsyncMock()
        agent_client.send_message = AsyncMock(return_value=("Reply", False))

        runner = SparringRunner(
            agent_client=agent_client,
            llm=mock_llm,
            test_case=test_case,
            system_prompt="System prompt",
        )

        conversation, reason, rounds = await runner.run()

        assert conversation[0]["content"] == "喂？"
        agent_client.send_message.assert_called_with("喂？")

    @pytest.mark.asyncio
    async def test_correct_round_count(self, mock_llm, test_case_factory):
        test_case = test_case_factory(max_rounds=4)

        agent_client = AsyncMock()
        agent_client.send_message = AsyncMock(
            side_effect=[
                ("Reply 1", False),
                ("Reply 2", False),
                ("Reply 3", True),  # Agent ends on round 3
            ]
        )

        mock_llm.chat_responses = [
            "Follow-up 1",
            "Follow-up 2",
        ]

        runner = SparringRunner(
            agent_client=agent_client,
            llm=mock_llm,
            test_case=test_case,
            system_prompt="Sparring prompt",
        )

        conversation, reason, rounds = await runner.run()

        assert rounds == 3
        assert reason == "agent_hangup"
        # 3 rounds = 3 user + 3 assistant = 6 messages
        assert len(conversation) == 6
