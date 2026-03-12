"""Builder Agent service — loads project context, calls LLM, returns response."""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError, ValidationError
from app.llm.base import LLMAdapter
from app.llm.factory import create_llm_adapter
from app.models.project import Project
from app.models.project_file import ProjectFile
from app.models.provider_config import ProviderConfig
from app.services.builder_conversation_service import append_message, get_or_create
from app.services.file_parser import parse_file

logger = logging.getLogger(__name__)

BUILDER_SYSTEM_PROMPT = """\
你是「构建助手」，一个对话 Agent 评测平台的内置 AI 助手。你的职责是帮助用户配置评测方案。

## 你的能力
- 理解用户的业务场景和评测意图
- 根据上传的文件（话术手册、业务流程等）提取关键信息
- 生成对练测试用例（角色描述）
- 生成裁判配置（Checklist 检查项 + Evaluation 评判维度）

## 交互原则
1. 主动引导：如果用户的描述不够具体，主动提问以获取关键信息
2. 分步确认：先生成用例，确认后再生成裁判配置
3. 专业但易懂：用用户能理解的语言解释配置含义
4. 不要越界：你只负责配置对练用例和裁判标准，不处理其他请求

## 当前限制
配置生成和写入功能将在后续版本中启用。当前你可以：
- 与用户讨论评测方案
- 分析上传的文件内容
- 提供配置建议
"""


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


async def chat(
    db: AsyncSession,
    project_id: UUID,
    user_message: str,
    provider_name: str,
    model_name: str,
) -> str:
    """Process a user message: call LLM, then save both user and assistant messages."""
    # Verify project exists
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("项目不存在")

    # Load context
    file_context = await _load_project_context(db, project_id)

    # Build system prompt with file context
    system_prompt = BUILDER_SYSTEM_PROMPT
    if file_context:
        system_prompt += f"\n\n## 项目文件内容\n以下是用户上传的项目文件，请结合这些内容理解业务场景：\n\n{file_context}"

    # Build messages: existing history + new user message
    conv = await get_or_create(db, project_id)
    messages = [{"role": m["role"], "content": m["content"]} for m in conv.messages]
    messages.append({"role": "user", "content": user_message})

    # Call LLM first — if this fails, no messages are persisted
    adapter = await _get_llm_adapter(db, provider_name, model_name)
    response = await adapter.chat(
        messages=messages,
        system_prompt=system_prompt,
        temperature=0.7,
        max_tokens=4096,
    )

    # Persist both messages only after successful LLM call
    await append_message(db, project_id, "user", user_message)
    await append_message(db, project_id, "assistant", response)

    return response
