from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.builder_conversation import (
    AppendMessageRequest,
    BuilderConversationResponse,
)
from app.services import builder_conversation_service

router = APIRouter(
    prefix="/api/projects/{project_id}/builder-conversation",
    tags=["builder-conversation"],
)


@router.get("", response_model=BuilderConversationResponse)
async def get_conversation(
    project_id: UUID, db: AsyncSession = Depends(get_db)
):
    return await builder_conversation_service.get_or_create(db, project_id)


@router.post("/messages", response_model=BuilderConversationResponse)
async def append_message(
    project_id: UUID,
    data: AppendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    return await builder_conversation_service.append_message(
        db, project_id, data.message.role, data.message.content
    )


@router.delete("/messages", response_model=BuilderConversationResponse)
async def clear_messages(
    project_id: UUID, db: AsyncSession = Depends(get_db)
):
    return await builder_conversation_service.clear(db, project_id)
