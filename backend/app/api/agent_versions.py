from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_project_access
from app.models.project import Project
from app.schemas.agent_version import AgentTestResult, AgentVersionCreate, AgentVersionResponse, AgentVersionUpdate
from app.services import agent_version_service

router = APIRouter(prefix="/api/projects/{project_id}/agent-versions", tags=["agent-versions"])


@router.get("", response_model=list[AgentVersionResponse])
async def list_agent_versions(project_id: UUID, db: AsyncSession = Depends(get_db), _: Project = Depends(verify_project_access)):
    """获取项目下所有 Agent 版本列表。"""
    return await agent_version_service.list_versions(db, project_id)


@router.post("", response_model=AgentVersionResponse, status_code=201)
async def create_agent_version(project_id: UUID, data: AgentVersionCreate, db: AsyncSession = Depends(get_db), _: Project = Depends(verify_project_access)):
    """创建新的 Agent 版本。"""
    return await agent_version_service.create_version(db, project_id, data)


@router.post("/test-unsaved", response_model=AgentTestResult)
async def test_unsaved_agent(project_id: UUID, data: AgentVersionCreate, _: Project = Depends(verify_project_access)):
    """使用未保存的表单数据测试 Agent 连通性（不写入数据库）。"""
    return await agent_version_service.test_connection_unsaved(data)


@router.put("/{version_id}", response_model=AgentVersionResponse)
async def update_agent_version(
    project_id: UUID, version_id: UUID, data: AgentVersionUpdate, db: AsyncSession = Depends(get_db), _: Project = Depends(verify_project_access)
):
    """更新指定 Agent 版本的配置信息。"""
    return await agent_version_service.update_version(db, project_id, version_id, data)


@router.delete("/{version_id}", status_code=204)
async def delete_agent_version(project_id: UUID, version_id: UUID, db: AsyncSession = Depends(get_db), _: Project = Depends(verify_project_access)):
    """删除指定 Agent 版本。"""
    await agent_version_service.delete_version(db, project_id, version_id)


@router.post("/{version_id}/test", response_model=AgentTestResult)
async def test_agent_connection(project_id: UUID, version_id: UUID, db: AsyncSession = Depends(get_db), _: Project = Depends(verify_project_access)):
    """测试 Agent 版本的 API 连通性。"""
    return await agent_version_service.test_connection(db, project_id, version_id)
