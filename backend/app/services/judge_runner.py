import json
import logging
from decimal import Decimal

from app.llm.base import LLMAdapter
from app.models.judge_config import ChecklistItem, EvalDimension

logger = logging.getLogger(__name__)


class JudgeResult:
    def __init__(
        self,
        checklist_results: list[dict],
        eval_scores: list[dict],
        summary: str,
        passed: bool,
    ):
        self.checklist_results = checklist_results
        self.eval_scores = eval_scores
        self.summary = summary
        self.passed = passed


class JudgeRunner:
    def __init__(
        self,
        llm: LLMAdapter,
        system_prompt: str,
        checklist_items: list[ChecklistItem],
        eval_dimensions: list[EvalDimension],
        pass_threshold: Decimal,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        self.llm = llm
        self.system_prompt = system_prompt
        self.checklist_items = checklist_items
        self.eval_dimensions = eval_dimensions
        self.pass_threshold = pass_threshold
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def judge(self, conversation: list[dict]) -> JudgeResult:
        prompt = self._build_prompt(conversation)

        # Call LLM with JSON mode, retry once on format error
        last_error = None
        for attempt in range(2):
            try:
                result = await self.llm.chat_json(
                    messages=[{"role": "user", "content": prompt}],
                    system_prompt=self.system_prompt,
                    temperature=self.temperature if self.temperature is not None else 0.0,
                    max_tokens=self.max_tokens if self.max_tokens is not None else 4096,
                )
                return self._parse_result(result)
            except ValueError as e:
                last_error = e
                if attempt == 0:
                    logger.warning(f"裁判 JSON 解析失败，重试: {e}")
                    continue
        raise ValueError(f"裁判输出格式错误（已重试）: {last_error}")

    def _build_prompt(self, conversation: list[dict]) -> str:
        parts = []

        # Checklist section
        if self.checklist_items:
            parts.append("--- Checklist ---")
            parts.append("请逐条判断以下检查项（回答\"是\"或\"否\"）：")
            for i, item in enumerate(self.checklist_items, 1):
                level_label = "🔴必过" if item.level == "must" else "🟡重要"
                parts.append(f"{i}. [{level_label}] {item.content}")

        # Evaluation section
        if self.eval_dimensions:
            parts.append("\n--- Evaluation ---")
            parts.append("请对以下维度打分（1-3 分）：")
            for dim in self.eval_dimensions:
                parts.append(f"\n维度：{dim.name}")
                if dim.description:
                    parts.append(f"说明：{dim.description}")
                if dim.level_3_desc:
                    parts.append(f"3 分：{dim.level_3_desc}")
                if dim.level_2_desc:
                    parts.append(f"2 分：{dim.level_2_desc}")
                if dim.level_1_desc:
                    parts.append(f"1 分：{dim.level_1_desc}")

        # Conversation
        parts.append("\n--- 对话记录 ---")
        for msg in conversation:
            role = "对练机器人" if msg["role"] == "user" else "Agent"
            parts.append(f"[{role}]: {msg['content']}")

        # Output format
        parts.append("\n--- 输出格式 ---")
        parts.append("请以 JSON 格式输出，包含以下字段：")
        parts.append(json.dumps({
            "checklist": [{"index": 1, "passed": True, "reason": "简要理由"}],
            "evaluation": [{"dimension": "维度名", "score": 3, "reason": "简要理由"}],
            "summary": "整体评价总结",
        }, ensure_ascii=False, indent=2))

        return "\n".join(parts)

    def _parse_result(self, result: dict) -> JudgeResult:
        # Parse checklist results
        checklist_results = []
        raw_checklist = result.get("checklist", [])
        for i, item in enumerate(self.checklist_items):
            raw = raw_checklist[i] if i < len(raw_checklist) else {}
            checklist_results.append({
                "content": item.content,
                "level": item.level,
                "passed": raw.get("passed", False),
                "reason": raw.get("reason", ""),
            })

        # Parse eval scores
        eval_scores = []
        raw_eval = result.get("evaluation", [])
        for i, dim in enumerate(self.eval_dimensions):
            raw = raw_eval[i] if i < len(raw_eval) else {}
            eval_scores.append({
                "dimension": dim.name,
                "score": raw.get("score", 1),
                "reason": raw.get("reason", ""),
            })

        summary = result.get("summary", "")

        # Determine pass/fail
        passed = self._check_passed(checklist_results, eval_scores)

        return JudgeResult(
            checklist_results=checklist_results,
            eval_scores=eval_scores,
            summary=summary,
            passed=passed,
        )

    def _check_passed(self, checklist_results: list[dict], eval_scores: list[dict]) -> bool:
        # All "must" checklist items must pass
        for item in checklist_results:
            if item["level"] == "must" and not item["passed"]:
                return False

        # Evaluation average >= threshold
        if eval_scores:
            avg = sum(s["score"] for s in eval_scores) / len(eval_scores)
            if avg < float(self.pass_threshold):
                return False

        return True
