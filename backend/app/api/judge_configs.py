from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.judge_config import JudgeConfig
from app.models.project import Project
from app.schemas.judge_config import JudgeConfigResponse, JudgeConfigUpdate
from app.services import judge_config_service

router = APIRouter(prefix="/api/projects/{project_id}/judge-config", tags=["judge-config"])


@router.get("/", response_model=JudgeConfigResponse | None)
async def get_judge_config(project_id: UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")

    result = await db.execute(
        select(JudgeConfig)
        .where(JudgeConfig.project_id == project_id)
        .options(selectinload(JudgeConfig.checklist_items), selectinload(JudgeConfig.eval_dimensions))
    )
    return result.scalar_one_or_none()


@router.put("/", response_model=JudgeConfigResponse)
async def update_judge_config(project_id: UUID, data: JudgeConfigUpdate, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")

    async with db.begin():
        config = await judge_config_service.save_judge_config(db, project_id, data)

    # Reload with relationships
    result = await db.execute(
        select(JudgeConfig)
        .where(JudgeConfig.id == config.id)
        .options(selectinload(JudgeConfig.checklist_items), selectinload(JudgeConfig.eval_dimensions))
    )
    return result.scalar_one()
