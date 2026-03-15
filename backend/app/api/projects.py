from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.project import (
    ConfigReadiness,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.services import project_service

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取当前用户的所有项目列表。"""
    return await project_service.list_projects(db, current_user.id)


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建新的评测项目。"""
    return await project_service.create_project(db, data, current_user.id)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取项目详情。"""
    return await project_service.get_project(db, project_id, current_user.id)


@router.get("/{project_id}/readiness", response_model=ConfigReadiness)
async def get_config_readiness(project_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """检查项目配置是否就绪（可发起批测的前置条件）。"""
    return await project_service.get_config_readiness(db, project_id, current_user.id)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: UUID, data: ProjectUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新项目基本信息。"""
    return await project_service.update_project(db, project_id, data, current_user.id)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除项目及其所有关联数据。"""
    await project_service.delete_project(db, project_id, current_user.id)
