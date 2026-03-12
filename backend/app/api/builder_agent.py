from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.builder_agent import BuilderChatRequest, BuilderChatResponse
from app.services import builder_agent_service

router = APIRouter(
    prefix="/api/projects/{project_id}/builder-agent",
    tags=["builder-agent"],
)


@router.post("/chat", response_model=BuilderChatResponse)
async def chat(
    project_id: UUID,
    data: BuilderChatRequest,
    db: AsyncSession = Depends(get_db),
):
    response = await builder_agent_service.chat(
        db, project_id, data.message, data.provider, data.model
    )
    return BuilderChatResponse(response=response)
