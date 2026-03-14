from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.judge_config import JudgeConfig
from app.models.project import Project
from app.models.user import User
from app.schemas.judge_config import JudgeConfigResponse, JudgeConfigUpdate
from app.services import judge_config_service

router = APIRouter(prefix="/api/projects/{project_id}/judge-config", tags=["judge-config"])


@router.get("", response_model=JudgeConfigResponse | None)
async def get_judge_config(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")

    result = await db.execute(
        select(JudgeConfig)
        .where(JudgeConfig.project_id == project_id)
        .options(selectinload(JudgeConfig.checklist_items), selectinload(JudgeConfig.eval_dimensions))
    )
    return result.scalar_one_or_none()


@router.put("", response_model=JudgeConfigResponse)
async def update_judge_config(project_id: UUID, data: JudgeConfigUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")

    config = await judge_config_service.save_judge_config(db, project_id, data)
    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(JudgeConfig)
        .where(JudgeConfig.id == config.id)
        .options(selectinload(JudgeConfig.checklist_items), selectinload(JudgeConfig.eval_dimensions))
    )
    return result.scalar_one()
