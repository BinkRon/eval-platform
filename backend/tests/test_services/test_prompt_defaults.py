"""Tests for default System Prompts: non-empty and contain key content."""
from app.services.prompt_defaults import DEFAULT_JUDGE_SYSTEM_PROMPT, DEFAULT_SPARRING_SYSTEM_PROMPT


class TestDefaultSparringPrompt:
    def test_non_empty(self):
        assert len(DEFAULT_SPARRING_SYSTEM_PROMPT.strip()) > 0

    def test_contains_role_instructions(self):
        assert "角色" in DEFAULT_SPARRING_SYSTEM_PROMPT

    def test_no_end_marker_duplication(self):
        """END marker is added by _build_persona_prompt, not in default system prompt."""
        assert "[END]" not in DEFAULT_SPARRING_SYSTEM_PROMPT

    def test_contains_natural_conversation_rule(self):
        assert "自然对话" in DEFAULT_SPARRING_SYSTEM_PROMPT

    def test_contains_no_cooperation_rule(self):
        assert "不要配合" in DEFAULT_SPARRING_SYSTEM_PROMPT


class TestDefaultJudgePrompt:
    def test_non_empty(self):
        assert len(DEFAULT_JUDGE_SYSTEM_PROMPT.strip()) > 0

    def test_contains_evidence_based(self):
        assert "基于证据" in DEFAULT_JUDGE_SYSTEM_PROMPT

    def test_contains_independent_judgment(self):
        assert "独立评判" in DEFAULT_JUDGE_SYSTEM_PROMPT

    def test_contains_checklist_instruction(self):
        assert "Checklist" in DEFAULT_JUDGE_SYSTEM_PROMPT

    def test_contains_evaluation_instruction(self):
        assert "Evaluation" in DEFAULT_JUDGE_SYSTEM_PROMPT

    def test_contains_output_format_instruction(self):
        assert "输出格式" in DEFAULT_JUDGE_SYSTEM_PROMPT
