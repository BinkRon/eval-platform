from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent_version import AgentVersion
from app.models.project import Project
from app.schemas.agent_version import AgentTestResult, AgentVersionCreate, AgentVersionResponse, AgentVersionUpdate
from app.services.agent_version_service import test_connection

router = APIRouter(prefix="/api/projects/{project_id}/agent-versions", tags=["agent-versions"])


def _to_response(v: AgentVersion) -> AgentVersionResponse:
    data = {c.key: getattr(v, c.key) for c in AgentVersion.__table__.columns if c.key != "auth_token"}
    data["auth_token_set"] = bool(v.auth_token)
    return AgentVersionResponse(**data)


async def _get_project(project_id: UUID, db: AsyncSession) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")
    return project


@router.get("", response_model=list[AgentVersionResponse])
async def list_agent_versions(project_id: UUID, db: AsyncSession = Depends(get_db)):
    await _get_project(project_id, db)
    result = await db.execute(
        select(AgentVersion).where(AgentVersion.project_id == project_id).order_by(AgentVersion.created_at.desc())
    )
    return [_to_response(v) for v in result.scalars().all()]


@router.post("", response_model=AgentVersionResponse, status_code=201)
async def create_agent_version(project_id: UUID, data: AgentVersionCreate, db: AsyncSession = Depends(get_db)):
    await _get_project(project_id, db)
    version = AgentVersion(project_id=project_id, **data.model_dump())
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return _to_response(version)


@router.put("/{version_id}", response_model=AgentVersionResponse)
async def update_agent_version(
    project_id: UUID, version_id: UUID, data: AgentVersionUpdate, db: AsyncSession = Depends(get_db)
):
    version = await db.get(AgentVersion, version_id)
    if not version or version.project_id != project_id:
        raise HTTPException(404, detail="Agent version not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(version, key, value)

    await db.commit()
    await db.refresh(version)
    return _to_response(version)


@router.delete("/{version_id}", status_code=204)
async def delete_agent_version(project_id: UUID, version_id: UUID, db: AsyncSession = Depends(get_db)):
    version = await db.get(AgentVersion, version_id)
    if not version or version.project_id != project_id:
        raise HTTPException(404, detail="Agent version not found")

    await db.delete(version)
    await db.commit()


@router.post("/{version_id}/test", response_model=AgentTestResult)
async def test_agent_connection(project_id: UUID, version_id: UUID, db: AsyncSession = Depends(get_db)):
    version = await db.get(AgentVersion, version_id)
    if not version or version.project_id != project_id:
        raise HTTPException(404, detail="Agent version not found")

    if not version.endpoint:
        raise HTTPException(400, detail="Agent endpoint not configured")

    return await test_connection(db, version)
