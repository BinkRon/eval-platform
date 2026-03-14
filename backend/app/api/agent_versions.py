from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.agent_version import AgentTestResult, AgentVersionCreate, AgentVersionResponse, AgentVersionUpdate
from app.services import agent_version_service

router = APIRouter(prefix="/api/projects/{project_id}/agent-versions", tags=["agent-versions"])


@router.get("", response_model=list[AgentVersionResponse])
async def list_agent_versions(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await agent_version_service.list_versions(db, project_id)


@router.post("", response_model=AgentVersionResponse, status_code=201)
async def create_agent_version(project_id: UUID, data: AgentVersionCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await agent_version_service.create_version(db, project_id, data)


@router.put("/{version_id}", response_model=AgentVersionResponse)
async def update_agent_version(
    project_id: UUID, version_id: UUID, data: AgentVersionUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)
):
    return await agent_version_service.update_version(db, project_id, version_id, data)


@router.delete("/{version_id}", status_code=204)
async def delete_agent_version(project_id: UUID, version_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    await agent_version_service.delete_version(db, project_id, version_id)


@router.post("/{version_id}/test", response_model=AgentTestResult)
async def test_agent_connection(project_id: UUID, version_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await agent_version_service.test_connection(db, project_id, version_id)
