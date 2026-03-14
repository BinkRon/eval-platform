from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_project_access
from app.models.project import Project
from app.schemas.builder_agent import (
    ApplyConfigRequest,
    ApplyConfigResponse,
    BuilderChatRequest,
    BuilderChatResponse,
)
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
    _: Project = Depends(verify_project_access),
):
    """与构建助手对话。返回文本回复和可选的确认卡片数据。"""
    result = await builder_agent_service.chat(
        db, project_id, data.message, data.provider, data.model
    )
    return BuilderChatResponse(**result)


@router.post("/apply-config", response_model=ApplyConfigResponse)
async def apply_config(
    project_id: UUID,
    data: ApplyConfigRequest,
    db: AsyncSession = Depends(get_db),
    _: Project = Depends(verify_project_access),
):
    """将构建助手生成的配置写入项目。用户确认后调用此接口。"""
    summary = await builder_agent_service.apply_generated_config(
        db, project_id, data.config_type, data.config_payload, data.mode
    )
    return ApplyConfigResponse(success=True, summary=summary)
