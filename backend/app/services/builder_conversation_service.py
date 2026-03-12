from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models.builder_conversation import BuilderConversation
from app.models.project import Project


async def _get_project(db: AsyncSession, project_id: UUID) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("项目不存在")
    return project


async def get_or_create(db: AsyncSession, project_id: UUID) -> BuilderConversation:
    """Get existing conversation or create a new empty one."""
    await _get_project(db, project_id)
    result = await db.execute(
        select(BuilderConversation).where(BuilderConversation.project_id == project_id)
    )
    conv = result.scalar_one_or_none()
    if conv:
        return conv

    conv = BuilderConversation(project_id=project_id, messages=[])
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def append_message(
    db: AsyncSession, project_id: UUID, role: str, content: str
) -> BuilderConversation:
    """Append a message to the conversation."""
    conv = await get_or_create(db, project_id)
    # JSONB mutation: create new list to trigger SQLAlchemy change detection
    new_messages = list(conv.messages) + [{"role": role, "content": content}]
    conv.messages = new_messages
    await db.commit()
    await db.refresh(conv)
    return conv


async def clear(db: AsyncSession, project_id: UUID) -> BuilderConversation:
    """Clear all messages in the conversation."""
    conv = await get_or_create(db, project_id)
    conv.messages = []
    await db.commit()
    await db.refresh(conv)
    return conv
