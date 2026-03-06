from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.model_config import ModelConfig
from app.models.project import Project
from app.schemas.model_config import ModelConfigResponse, ModelConfigUpdate

router = APIRouter(prefix="/api/projects/{project_id}/model-config", tags=["model-config"])


@router.get("/", response_model=ModelConfigResponse | None)
async def get_model_config(project_id: UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")

    result = await db.execute(select(ModelConfig).where(ModelConfig.project_id == project_id))
    return result.scalar_one_or_none()


@router.put("/", response_model=ModelConfigResponse)
async def update_model_config(project_id: UUID, data: ModelConfigUpdate, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")

    result = await db.execute(select(ModelConfig).where(ModelConfig.project_id == project_id))
    config = result.scalar_one_or_none()

    if not config:
        config = ModelConfig(project_id=project_id, **data.model_dump(exclude_unset=True))
        db.add(config)
    else:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(config, key, value)

    await db.commit()
    return config
