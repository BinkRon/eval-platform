"""Tests for JudgeRunner: prompt building, result parsing, pass/fail logic, full flow."""
import pytest

from app.models.judge_config import ChecklistItem, EvalDimension
from app.services.judge_runner import JudgeRunner


# ---------------------------------------------------------------------------
# TestBuildPrompt
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    """Verify _build_prompt assembles the correct prompt text."""

    def _make_runner(self, checklist_items, eval_dimensions, mock_llm):
        return JudgeRunner(
            llm=mock_llm,
            system_prompt="You are a judge.",
            checklist_items=checklist_items,
            eval_dimensions=eval_dimensions,
            pass_threshold=2.0,
        )

    def test_includes_checklist_items(self, mock_llm, checklist_item_factory):
        items = [
            checklist_item_factory(content="Agent greeted user", level="must"),
            checklist_item_factory(content="Agent asked clarification", level="important"),
        ]
        runner = self._make_runner(items, [], mock_llm)
        prompt = runner._build_prompt([{"role": "user", "content": "hi"}])

        assert "Agent greeted user" in prompt
        assert "Agent asked clarification" in prompt
        assert "必过" in prompt
        assert "重要" in prompt

    def test_includes_eval_dimensions(self, mock_llm, eval_dimension_factory):
        dims = [
            eval_dimension_factory(
                name="Helpfulness",
                description="How helpful",
                level_3_desc="Excellent",
                level_2_desc="OK",
                level_1_desc="Poor",
            ),
        ]
        runner = self._make_runner([], dims, mock_llm)
        prompt = runner._build_prompt([{"role": "user", "content": "hi"}])

        assert "Helpfulness" in prompt
        assert "How helpful" in prompt
        assert "Excellent" in prompt
        assert "OK" in prompt
        assert "Poor" in prompt

    def test_includes_conversation(self, mock_llm, sample_conversation):
        runner = self._make_runner([], [], mock_llm)
        prompt = runner._build_prompt(sample_conversation)

        # User messages appear as 对练机器人, assistant as Agent
        assert "[对练机器人]" in prompt
        assert "[Agent]" in prompt
        assert "order #12345" in prompt

    def test_includes_json_output_format(self, mock_llm):
        runner = self._make_runner([], [], mock_llm)
        prompt = runner._build_prompt([{"role": "user", "content": "hi"}])

        assert "JSON" in prompt
        assert "checklist" in prompt
        assert "evaluation" in prompt
        assert "summary" in prompt


# ---------------------------------------------------------------------------
# TestParseResult
# ---------------------------------------------------------------------------


class TestParseResult:
    """Verify _parse_result correctly maps LLM JSON to JudgeResult."""

    def _make_runner(self, checklist_items, eval_dimensions, mock_llm):
        return JudgeRunner(
            llm=mock_llm,
            system_prompt="You are a judge.",
            checklist_items=checklist_items,
            eval_dimensions=eval_dimensions,
            pass_threshold=2.0,
        )

    def test_parse_complete_result(self, mock_llm, checklist_item_factory, eval_dimension_factory):
        items = [
            checklist_item_factory(content="Greeted user", level="must"),
            checklist_item_factory(content="Solved problem", level="important"),
        ]
        dims = [
            eval_dimension_factory(name="Helpfulness"),
            eval_dimension_factory(name="Accuracy"),
        ]
        runner = self._make_runner(items, dims, mock_llm)

        raw = {
            "checklist": [
                {"index": 1, "passed": True, "reason": "Said hello"},
                {"index": 2, "passed": False, "reason": "Did not solve"},
            ],
            "evaluation": [
                {"dimension": "Helpfulness", "score": 3, "reason": "Very helpful"},
                {"dimension": "Accuracy", "score": 2, "reason": "Mostly accurate"},
            ],
            "summary": "Overall good performance.",
        }

        result = runner._parse_result(raw)

        assert len(result.checklist_results) == 2
        assert result.checklist_results[0]["passed"] is True
        assert result.checklist_results[0]["content"] == "Greeted user"
        assert result.checklist_results[1]["passed"] is False
        assert len(result.eval_scores) == 2
        assert result.eval_scores[0]["score"] == 3
        assert result.eval_scores[1]["dimension"] == "Accuracy"
        assert result.summary == "Overall good performance."

    def test_parse_result_index_mismatch_falls_back(self, mock_llm, checklist_item_factory):
        items = [
            checklist_item_factory(content="Item A", level="must"),
            checklist_item_factory(content="Item B", level="must"),
        ]
        runner = self._make_runner(items, [], mock_llm)

        # LLM returns wrong index values — should fall back to positional
        raw = {
            "checklist": [
                {"index": 10, "passed": True, "reason": "reason A"},
                {"index": 20, "passed": False, "reason": "reason B"},
            ],
            "evaluation": [],
            "summary": "test",
        }

        result = runner._parse_result(raw)

        # Falls back to positional: items[0] → checklist[0], items[1] → checklist[1]
        assert result.checklist_results[0]["passed"] is True
        assert result.checklist_results[0]["content"] == "Item A"
        assert result.checklist_results[1]["passed"] is False
        assert result.checklist_results[1]["content"] == "Item B"


# ---------------------------------------------------------------------------
# TestCheckPassed
# ---------------------------------------------------------------------------


class TestCheckPassed:
    """Verify _check_passed logic for must items and eval threshold."""

    def _make_runner(self, mock_llm, threshold=2.0):
        return JudgeRunner(
            llm=mock_llm,
            system_prompt="judge",
            checklist_items=[],
            eval_dimensions=[],
            pass_threshold=threshold,
        )

    def test_all_must_pass(self, mock_llm):
        runner = self._make_runner(mock_llm)
        checklist = [
            {"content": "A", "level": "must", "passed": True, "reason": ""},
            {"content": "B", "level": "must", "passed": True, "reason": ""},
        ]
        assert runner._check_passed(checklist, []) is True

    def test_must_failure(self, mock_llm):
        runner = self._make_runner(mock_llm)
        checklist = [
            {"content": "A", "level": "must", "passed": True, "reason": ""},
            {"content": "B", "level": "must", "passed": False, "reason": ""},
        ]
        assert runner._check_passed(checklist, []) is False

    def test_eval_below_threshold(self, mock_llm):
        runner = self._make_runner(mock_llm, threshold=2.5)
        eval_scores = [
            {"dimension": "D1", "score": 2, "reason": ""},
            {"dimension": "D2", "score": 2, "reason": ""},
        ]
        # avg = 2.0 < 2.5 → fail
        assert runner._check_passed([], eval_scores) is False

    def test_eval_at_threshold(self, mock_llm):
        runner = self._make_runner(mock_llm, threshold=2.0)
        eval_scores = [
            {"dimension": "D1", "score": 2, "reason": ""},
            {"dimension": "D2", "score": 2, "reason": ""},
        ]
        # avg = 2.0 == 2.0 → pass
        assert runner._check_passed([], eval_scores) is True

    def test_no_criteria(self, mock_llm):
        runner = self._make_runner(mock_llm)
        assert runner._check_passed([], []) is True


# ---------------------------------------------------------------------------
# TestJudgeFlow
# ---------------------------------------------------------------------------


class TestJudgeFlow:
    """End-to-end tests for the judge() method."""

    @pytest.mark.asyncio
    async def test_successful_judge(self, mock_llm, checklist_item_factory, eval_dimension_factory, sample_conversation):
        items = [checklist_item_factory(content="Greeted", level="must")]
        dims = [eval_dimension_factory(name="Quality")]

        mock_llm.chat_json_responses = [{
            "checklist": [{"index": 1, "passed": True, "reason": "ok"}],
            "evaluation": [{"dimension": "Quality", "score": 3, "reason": "good"}],
            "summary": "Passed.",
        }]

        runner = JudgeRunner(
            llm=mock_llm,
            system_prompt="Judge system prompt",
            checklist_items=items,
            eval_dimensions=dims,
            pass_threshold=2.0,
        )

        result = await runner.judge(sample_conversation)

        assert result.passed is True
        assert result.summary == "Passed."
        assert mock_llm.chat_json_call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_parse_failure(self, mock_llm, checklist_item_factory, eval_dimension_factory, sample_conversation):
        items = [checklist_item_factory(content="Greeted", level="must")]
        dims = [eval_dimension_factory(name="Quality")]

        # First response raises ValueError during parse (missing fields triggers fallback),
        # but we need chat_json itself to raise. We'll make first response raise ValueError.
        mock_llm.chat_json_responses = [
            ValueError("invalid json"),  # Will be raised
            {
                "checklist": [{"index": 1, "passed": True, "reason": "ok"}],
                "evaluation": [{"dimension": "Quality", "score": 3, "reason": "good"}],
                "summary": "Retry success.",
            },
        ]

        # Override chat_json to raise on ValueError sentinel
        original_chat_json = mock_llm.chat_json

        async def patched_chat_json(**kwargs):
            mock_llm.chat_json_call_count += 1
            mock_llm.chat_json_call_args.append(kwargs)
            if not mock_llm.chat_json_responses:
                raise ValueError("MockLLMAdapter: chat_json_responses exhausted")
            resp = mock_llm.chat_json_responses.pop(0)
            if isinstance(resp, Exception):
                raise resp
            return resp

        mock_llm.chat_json = patched_chat_json

        runner = JudgeRunner(
            llm=mock_llm,
            system_prompt="Judge",
            checklist_items=items,
            eval_dimensions=dims,
            pass_threshold=2.0,
        )

        result = await runner.judge(sample_conversation)

        assert result.passed is True
        assert result.summary == "Retry success."
        assert mock_llm.chat_json_call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_two_failures(self, mock_llm, checklist_item_factory, eval_dimension_factory, sample_conversation):
        items = [checklist_item_factory(content="Greeted", level="must")]
        dims = [eval_dimension_factory(name="Quality")]

        # Both attempts raise ValueError
        mock_llm.chat_json_responses = [
            ValueError("bad json 1"),
            ValueError("bad json 2"),
        ]

        async def patched_chat_json(**kwargs):
            mock_llm.chat_json_call_count += 1
            mock_llm.chat_json_call_args.append(kwargs)
            if not mock_llm.chat_json_responses:
                raise ValueError("MockLLMAdapter: chat_json_responses exhausted")
            resp = mock_llm.chat_json_responses.pop(0)
            if isinstance(resp, Exception):
                raise resp
            return resp

        mock_llm.chat_json = patched_chat_json

        runner = JudgeRunner(
            llm=mock_llm,
            system_prompt="Judge",
            checklist_items=items,
            eval_dimensions=dims,
            pass_threshold=2.0,
        )

        with pytest.raises(ValueError, match="裁判输出格式错误"):
            await runner.judge(sample_conversation)

        assert mock_llm.chat_json_call_count == 2
