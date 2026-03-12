"""Builder Agent service — loads project context, calls LLM, returns response.

Implements the "builder agent" intelligence layer:
- System prompt with Skill definitions (test case generation + judge config generation)
- Structured output parsing (extract JSON config blocks from LLM response)
- Config application (write generated configs to DB via existing services)
"""
import json
import logging
import re
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import NotFoundError, ValidationError
from app.llm.base import LLMAdapter
from app.llm.factory import create_llm_adapter
from app.models.judge_config import JudgeConfig
from app.models.project import Project
from app.models.project_file import ProjectFile
from app.models.provider_config import ProviderConfig
from app.models.test_case import TestCase
from app.schemas.judge_config import ChecklistItemData, EvalDimensionData, JudgeConfigUpdate
from app.services import judge_config_service
from app.services.builder_conversation_service import append_message, get_or_create
from app.services.file_parser import parse_file

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System Prompt with Skill definitions (PRD §4.2 + §4.3)
# ---------------------------------------------------------------------------

BUILDER_SYSTEM_PROMPT = """\
你是「构建助手」，一个对话 Agent 评测平台的内置 AI 助手。
你的职责是帮助用户配置评测方案——包括对练测试用例和裁判配置。

## 交互原则
1. **主动引导**：如果用户的描述不够具体，主动提问以获取关键信息。
2. **分步生成**：默认先生成对练用例，用户确认后再生成裁判配置。如果用户明确指定顺序，遵从用户意图。
3. **专业但易懂**：用用户能理解的语言解释配置含义。
4. **不要越界**：你只负责配置对练用例和裁判标准，不处理其他请求。

## Skill 一：对练用例生成

### 任务
根据用户描述的业务场景和上传的文件，生成一组对练测试用例。

### 输出格式
当你准备好生成对练用例时，请在回复中包含如下 XML 标签包裹的 JSON 配置块：

<generated_config>
{
  "config_type": "test_cases",
  "test_cases": [
    {
      "name": "用例名称",
      "sparring_prompt": "完整的角色描述（markdown 格式）",
      "first_message": "开场白，默认为'喂？'"
    }
  ]
}
</generated_config>

每条用例包含以下字段：
- name（字符串，必填）：简短的用例名称，应能体现角色的核心特征
- sparring_prompt（字符串，必填，markdown 格式）：完整的角色描述
- first_message（字符串，选填，默认"喂？"）：对练机器人的开场白

### sparring_prompt 的质量标准
一个好的角色描述应包含以下要素（不必严格按此结构，但需覆盖）：
- **角色身份**：年龄、职业、经济状况等基本画像
- **核心诉求**：这次对话要解决什么问题
- **性格与沟通风格**：说话方式、表达习惯、对专业术语的接受度
- **行为规则**：在特定条件下的反应模式（如"Agent 连续推销时会不耐烦"）
- **背景故事**（如有）：影响角色态度的过往经历

### 生成原则
- **多样性**：用例集应覆盖不同类型的用户画像，避免同质化
- **压力测试**：至少包含 1-2 个对 Agent 构成挑战的角色（如情绪化、不信任、知识空白）
- **真实感**：角色的行为逻辑应自洽，不要设定矛盾的特征
- **场景覆盖**：如果用户上传了话术手册或任务流程，用例应覆盖其中的关键分支

### 数量指引
- 用户未指定数量时，默认生成 5-8 条
- 可根据业务复杂度调整

## Skill 二：裁判配置生成

### 任务
根据用户描述的质量关注点和上传的文件，生成 Checklist 检查项和 Evaluation 评判维度。

### 输出格式
当你准备好生成裁判配置时，请在回复中包含如下 XML 标签包裹的 JSON 配置块：

<generated_config>
{
  "config_type": "judge_config",
  "checklist_items": [
    {"content": "检查问题", "level": "required 或 important"}
  ],
  "eval_dimensions": [
    {"name": "维度名称", "judge_prompt_segment": "评判指引（markdown 格式）"}
  ],
  "pass_threshold": 2.0
}
</generated_config>

### Checklist 字段
每条检查项包含：
- content（字符串）：一个可以回答"是"或"否"的明确问题
- level（枚举：required / important）：
  - required（必过）：红线项，违反即不通过
  - important（重要）：影响整体评分但不一票否决

### Checklist 质量标准
- **可判定**：基于对话内容可以明确回答是/否，不依赖外部信息
- **不重叠**：检查项之间不应有显著重复
- **分级合理**：红线项应限于合规底线和严重质量问题，不宜过多（建议不超过总数的 1/3）
- **粒度适中**：不宜过细或过粗

### Evaluation 字段
每个维度包含：
- name（字符串）：维度名称，简短明确
- judge_prompt_segment（字符串，markdown 格式）：评判指引

### judge_prompt_segment 的质量标准
一个好的评判指引应包含：
- **维度定义**：这个维度评判的是什么
- **评分锚点**：1 分、2 分、3 分各对应什么水平的表现（必须包含）
- **边界情况**（建议）：容易误判的情况及正确处理方式
- **正反例**（可选）：典型的好表现和差表现描述

### 生成原则
- **Checklist 与 Evaluation 互补**：Checklist 覆盖硬性合规要求，Evaluation 覆盖软性质量维度
- **维度正交**：Evaluation 维度之间应尽量独立，避免高度相关
- **总量可控**：Checklist 建议 3-8 条，Evaluation 维度建议 2-5 个
- **参考用例**：如果已有对练用例，裁判配置应与用例场景匹配
- **通过阈值**：默认 pass_threshold 为 2.0（3 分满分），可根据用户的质量标准调整

## 重要规则
- 每次回复最多包含一个 <generated_config> 块。
- 在 <generated_config> 块之前，必须先用自然语言说明你生成了什么以及关键信息摘要。
- 不要在普通对话中输出 <generated_config> 标签。只有当你确实准备好了完整的配置数据时才输出。
- JSON 必须是合法的 JSON 格式。字符串值中如有换行请使用 \\n 转义。
"""

# Config block parsing regex
_CONFIG_BLOCK_RE = re.compile(
    r"<generated_config>\s*(.*?)\s*</generated_config>",
    re.DOTALL,
)


async def _load_project_context(db: AsyncSession, project_id: UUID) -> str:
    """Load project files as context string."""
    result = await db.execute(
        select(ProjectFile)
        .where(ProjectFile.project_id == project_id)
        .order_by(ProjectFile.created_at)
    )
    files = result.scalars().all()
    if not files:
        return ""

    parts = []
    for f in files:
        content = parse_file(f.storage_path, f.file_type)
        if content:
            parts.append(f"--- 文件: {f.filename} ---\n{content}")

    if not parts:
        return ""
    return "\n\n".join(parts)


async def _get_llm_adapter(db: AsyncSession, provider_name: str, model_name: str) -> LLMAdapter:
    """Create an LLM adapter from provider config."""
    result = await db.execute(
        select(ProviderConfig).where(
            ProviderConfig.provider_name == provider_name,
            ProviderConfig.is_active.is_(True),
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise ValidationError(f"LLM 供应商 '{provider_name}' 未配置或未启用")
    if not provider.api_key:
        raise ValidationError(f"LLM 供应商 '{provider_name}' 未配置 API Key")
    return create_llm_adapter(
        provider_name=provider.provider_name,
        api_key=provider.api_key,
        model=model_name,
        base_url=provider.base_url,
    )


def parse_config_block(response: str) -> tuple[str, dict | None]:
    """Extract a <generated_config> JSON block from the LLM response.

    Returns:
        (clean_message, config_data) where clean_message has the config block removed
        and config_data is the parsed JSON dict, or None if no valid block found.
    """
    match = _CONFIG_BLOCK_RE.search(response)
    if not match:
        return response, None

    json_str = match.group(1)
    try:
        config_data = json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning("Failed to parse config block JSON: %s", json_str[:200])
        return response, None

    # Validate required field
    if not isinstance(config_data, dict) or "config_type" not in config_data:
        logger.warning("Config block missing 'config_type' field")
        return response, None

    config_type = config_data["config_type"]
    if config_type not in ("test_cases", "judge_config"):
        logger.warning("Unknown config_type: %s", config_type)
        return response, None

    # Remove the config block from the message text
    clean_message = response[: match.start()] + response[match.end() :]
    clean_message = clean_message.strip()

    return clean_message, config_data


def _build_test_cases_card_data(
    config_data: dict, existing_count: int
) -> dict:
    """Build card_data for test_cases generation."""
    test_cases = config_data.get("test_cases", [])
    items = []
    for tc in test_cases:
        name = tc.get("name", "未命名")
        prompt = tc.get("sparring_prompt", "")
        summary = prompt[:60] + "..." if len(prompt) > 60 else prompt
        items.append({
            "name": name,
            "summary": summary,
            "fullContent": prompt,
        })

    return {
        "config_type": "test_cases",
        "title": f"对练用例（{len(test_cases)} 条）",
        "items": items,
        "impact_message": f"将写入到「测试用例集」，当前已有 {existing_count} 条用例",
        "existing_count": existing_count,
        "config_payload": config_data,
    }


def _build_judge_config_card_data(
    config_data: dict,
    existing_checklist_count: int,
    existing_dimension_count: int,
) -> dict:
    """Build card_data for judge_config generation."""
    checklist_items = config_data.get("checklist_items", [])
    eval_dimensions = config_data.get("eval_dimensions", [])
    items = []
    for ci in checklist_items:
        level_label = "必过" if ci.get("level") == "required" else "重要"
        items.append({
            "name": f"[{level_label}] {ci.get('content', '')[:40]}",
            "summary": "",
            "fullContent": ci.get("content", ""),
        })
    for ed in eval_dimensions:
        segment = ed.get("judge_prompt_segment", "")
        items.append({
            "name": f"维度: {ed.get('name', '')}",
            "summary": segment[:60] + "..." if len(segment) > 60 else segment,
            "fullContent": segment,
        })

    return {
        "config_type": "judge_config",
        "title": f"裁判配置（{len(checklist_items)} 检查项 + {len(eval_dimensions)} 维度）",
        "items": items,
        "impact_message": (
            f"将写入到「裁判配置」，当前已有 {existing_checklist_count} 条检查项 + "
            f"{existing_dimension_count} 个评判维度"
        ),
        "existing_count": existing_checklist_count + existing_dimension_count,
        "existing_checklist_count": existing_checklist_count,
        "existing_dimension_count": existing_dimension_count,
        "new_checklist_count": len(checklist_items),
        "new_dimension_count": len(eval_dimensions),
        "config_payload": config_data,
    }


async def _get_existing_counts(
    db: AsyncSession, project_id: UUID, config_type: str
) -> dict:
    """Get counts of existing configs for impact message."""
    if config_type == "test_cases":
        result = await db.execute(
            select(func.count()).select_from(TestCase).where(
                TestCase.project_id == project_id
            )
        )
        return {"test_case_count": result.scalar() or 0}
    elif config_type == "judge_config":
        result = await db.execute(
            select(JudgeConfig)
            .where(JudgeConfig.project_id == project_id)
            .options(
                selectinload(JudgeConfig.checklist_items),
                selectinload(JudgeConfig.eval_dimensions),
            )
        )
        config = result.scalar_one_or_none()
        if not config:
            return {"checklist_count": 0, "dimension_count": 0}
        return {
            "checklist_count": len(config.checklist_items),
            "dimension_count": len(config.eval_dimensions),
        }
    return {}


async def build_card_data(
    db: AsyncSession, project_id: UUID, config_data: dict
) -> tuple[str, dict]:
    """Determine card_type and build card_data from parsed config.

    Returns:
        (card_type, card_data)
    """
    config_type = config_data["config_type"]
    counts = await _get_existing_counts(db, project_id, config_type)

    if config_type == "test_cases":
        card_data = _build_test_cases_card_data(
            config_data, counts.get("test_case_count", 0)
        )
        return "generate_confirm", card_data
    else:
        card_data = _build_judge_config_card_data(
            config_data,
            counts.get("checklist_count", 0),
            counts.get("dimension_count", 0),
        )
        return "generate_confirm", card_data


async def chat(
    db: AsyncSession,
    project_id: UUID,
    user_message: str,
    provider_name: str,
    model_name: str,
) -> dict:
    """Process a user message: call LLM, parse response, return structured result.

    Returns:
        dict with keys: response (str), card_type (str|None), card_data (dict|None)
    """
    # Verify project exists
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("项目不存在")

    # Load context
    file_context = await _load_project_context(db, project_id)

    # Build system prompt with file context
    system_prompt = BUILDER_SYSTEM_PROMPT
    if file_context:
        system_prompt += (
            "\n\n## 项目文件内容\n"
            "以下是用户上传的项目文件，请结合这些内容理解业务场景：\n\n"
            f"{file_context}"
        )

    # Build messages: existing history + new user message
    conv = await get_or_create(db, project_id)
    messages = [{"role": m["role"], "content": m["content"]} for m in conv.messages]
    messages.append({"role": "user", "content": user_message})

    # Call LLM first — if this fails, no messages are persisted
    adapter = await _get_llm_adapter(db, provider_name, model_name)
    raw_response = await adapter.chat(
        messages=messages,
        system_prompt=system_prompt,
        temperature=0.7,
        max_tokens=4096,
    )

    # Parse for config blocks
    clean_message, config_data = parse_config_block(raw_response)

    # If config block found but JSON parse failed, retry with chat_json
    if _CONFIG_BLOCK_RE.search(raw_response) and config_data is None:
        logger.info("Config block detected but parsing failed, retrying with chat_json")
        try:
            json_response = await adapter.chat_json(
                messages=messages,
                system_prompt=system_prompt + (
                    "\n\n## 重要：请以合法的 JSON 格式输出配置块内容。"
                    "不要包含 <generated_config> 标签，直接输出 JSON 对象。"
                ),
                temperature=0.3,
                max_tokens=4096,
            )
            if isinstance(json_response, dict) and "config_type" in json_response:
                config_data = json_response
                # Keep the clean message from original response (without broken block)
                clean_message = _CONFIG_BLOCK_RE.sub("", raw_response).strip()
        except Exception:
            logger.warning("chat_json retry also failed, returning text response")

        # Fallback: strip config block tags from message to avoid raw XML in frontend
        if config_data is None:
            clean_message = _CONFIG_BLOCK_RE.sub("", raw_response).strip()

    # Persist both messages only after successful LLM call
    # Store the raw response (with config block) for conversation history
    await append_message(db, project_id, "user", user_message)
    await append_message(db, project_id, "assistant", raw_response)

    # Build card data if config was generated
    card_type = None
    card_data_result = None
    if config_data is not None:
        card_type, card_data_result = await build_card_data(
            db, project_id, config_data
        )

    return {
        "response": clean_message,
        "card_type": card_type,
        "card_data": card_data_result,
    }


# ---------------------------------------------------------------------------
# Config application (6-3)
# ---------------------------------------------------------------------------

async def apply_generated_config(
    db: AsyncSession,
    project_id: UUID,
    config_type: str,
    config_payload: dict,
    mode: str = "append",
) -> dict:
    """Apply generated config to the project.

    Args:
        db: Database session
        project_id: Target project ID
        config_type: "test_cases" or "judge_config"
        config_payload: The config data from card_data.config_payload
        mode: "append" (add to existing) or "replace" (delete existing first)

    Returns:
        dict with summary of applied changes
    """
    # Verify project exists
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("项目不存在")

    if config_type == "test_cases":
        return await _apply_test_cases(db, project_id, config_payload, mode)
    elif config_type == "judge_config":
        return await _apply_judge_config(db, project_id, config_payload, mode)
    else:
        raise ValidationError(f"不支持的配置类型: {config_type}")


async def _apply_test_cases(
    db: AsyncSession, project_id: UUID, config_payload: dict, mode: str,
) -> dict:
    """Apply test cases config.

    Uses direct ORM operations (not test_case_service.create_test_case) to keep
    all inserts in a single transaction — either all succeed or none persist.
    """
    test_cases_data = config_payload.get("test_cases", [])
    if not test_cases_data:
        raise ValidationError("没有可写入的测试用例")

    # Replace mode: delete existing test cases first
    if mode == "replace":
        existing = await db.execute(
            select(TestCase).where(TestCase.project_id == project_id)
        )
        for tc in existing.scalars().all():
            await db.delete(tc)
        await db.flush()

    # Get current max sort_order for append mode
    sort_offset = 0
    if mode == "append":
        result = await db.execute(
            select(func.max(TestCase.sort_order)).where(
                TestCase.project_id == project_id
            )
        )
        max_order = result.scalar()
        sort_offset = (max_order or 0) + 1

    # Create all test cases in a single transaction
    for i, tc_data in enumerate(test_cases_data):
        name = tc_data.get("name")
        sparring_prompt = tc_data.get("sparring_prompt")
        if not name or not sparring_prompt:
            raise ValidationError(
                f"用例 #{i + 1} 缺少必填字段 name 或 sparring_prompt"
            )
        tc = TestCase(
            project_id=project_id,
            name=name,
            sparring_prompt=sparring_prompt,
            first_message=tc_data.get("first_message"),
            sort_order=sort_offset + i,
        )
        db.add(tc)

    await db.commit()
    return {"created": len(test_cases_data), "mode": mode}


async def _apply_judge_config(
    db: AsyncSession, project_id: UUID, config_payload: dict, mode: str,
) -> dict:
    """Apply judge config."""
    checklist_items = config_payload.get("checklist_items", [])
    eval_dimensions = config_payload.get("eval_dimensions", [])
    pass_threshold = config_payload.get("pass_threshold", 2.0)

    if not checklist_items and not eval_dimensions:
        raise ValidationError("没有可写入的裁判配置")

    # Map level values: required→must, important→should (match DB enum)
    level_map = {"required": "must", "important": "should"}

    if mode == "append":
        # Load existing config to merge
        result = await db.execute(
            select(JudgeConfig)
            .where(JudgeConfig.project_id == project_id)
            .options(
                selectinload(JudgeConfig.checklist_items),
                selectinload(JudgeConfig.eval_dimensions),
            )
        )
        existing = result.scalar_one_or_none()

        existing_cl = []
        existing_ed = []
        existing_threshold = pass_threshold
        if existing:
            existing_threshold = existing.pass_threshold
            for item in existing.checklist_items:
                existing_cl.append(ChecklistItemData(
                    content=item.content,
                    level=item.level,
                    sort_order=item.sort_order,
                ))
            for dim in existing.eval_dimensions:
                existing_ed.append(EvalDimensionData(
                    name=dim.name,
                    judge_prompt_segment=dim.judge_prompt_segment,
                    sort_order=dim.sort_order,
                ))

        # Append new items with offset sort_order
        cl_offset = max((c.sort_order for c in existing_cl), default=-1) + 1
        ed_offset = max((e.sort_order for e in existing_ed), default=-1) + 1

        for i, ci in enumerate(checklist_items):
            existing_cl.append(ChecklistItemData(
                content=ci["content"],
                level=level_map.get(ci.get("level", "important"), "should"),
                sort_order=cl_offset + i,
            ))
        for i, ed in enumerate(eval_dimensions):
            existing_ed.append(EvalDimensionData(
                name=ed["name"],
                judge_prompt_segment=ed["judge_prompt_segment"],
                sort_order=ed_offset + i,
            ))

        update_data = JudgeConfigUpdate(
            pass_threshold=existing_threshold,
            checklist_items=existing_cl,
            eval_dimensions=existing_ed,
        )
    else:
        # Replace mode: new config only
        cl_items = [
            ChecklistItemData(
                content=ci["content"],
                level=level_map.get(ci.get("level", "important"), "should"),
                sort_order=i,
            )
            for i, ci in enumerate(checklist_items)
        ]
        ed_items = [
            EvalDimensionData(
                name=ed["name"],
                judge_prompt_segment=ed["judge_prompt_segment"],
                sort_order=i,
            )
            for i, ed in enumerate(eval_dimensions)
        ]
        update_data = JudgeConfigUpdate(
            pass_threshold=pass_threshold,
            checklist_items=cl_items,
            eval_dimensions=ed_items,
        )

    await judge_config_service.save_judge_config(db, project_id, update_data)
    await db.commit()

    return {
        "checklist_count": len(checklist_items),
        "dimension_count": len(eval_dimensions),
        "mode": mode,
    }
