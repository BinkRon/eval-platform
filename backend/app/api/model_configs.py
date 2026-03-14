from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.model_config import ModelConfigResponse, ModelConfigUpdate
from app.services import model_config_service

router = APIRouter(prefix="/api/projects/{project_id}/model-config", tags=["model-config"])


@router.get("", response_model=ModelConfigResponse | None)
async def get_model_config(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await model_config_service.get_model_config(db, project_id)


@router.put("", response_model=ModelConfigResponse)
async def update_model_config(project_id: UUID, data: ModelConfigUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await model_config_service.upsert_model_config(db, project_id, data)
