from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models.model_config import ModelConfig
from app.models.project import Project
from app.schemas.model_config import ModelConfigUpdate


async def _get_project(db: AsyncSession, project_id: UUID) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("项目不存在")
    return project


async def get_model_config(db: AsyncSession, project_id: UUID) -> ModelConfig | None:
    await _get_project(db, project_id)
    result = await db.execute(select(ModelConfig).where(ModelConfig.project_id == project_id))
    return result.scalar_one_or_none()


async def upsert_model_config(db: AsyncSession, project_id: UUID, data: ModelConfigUpdate) -> ModelConfig:
    await _get_project(db, project_id)
    result = await db.execute(select(ModelConfig).where(ModelConfig.project_id == project_id))
    config = result.scalar_one_or_none()

    if not config:
        config = ModelConfig(project_id=project_id, **data.model_dump(exclude_unset=True))
        db.add(config)
    else:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(config, key, value)

    await db.commit()
    await db.refresh(config)
    return config
