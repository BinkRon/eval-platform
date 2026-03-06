import re
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_version import AgentVersion
from app.models.project import Project
from app.schemas.agent_version import (
    AgentTestResult,
    AgentVersionCreate,
    AgentVersionResponse,
    AgentVersionUpdate,
)
from app.services.agent_client import AgentClient

_IP_PATTERN = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")


def _sanitize_error(msg: str) -> str:
    return _IP_PATTERN.sub("[内部地址]", msg)


def _to_response(v: AgentVersion) -> AgentVersionResponse:
    data = {c.key: getattr(v, c.key) for c in AgentVersion.__table__.columns if c.key != "auth_token"}
    data["auth_token_set"] = bool(v.auth_token)
    return AgentVersionResponse(**data)


async def _get_project(db: AsyncSession, project_id: UUID) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")
    return project


async def list_versions(db: AsyncSession, project_id: UUID) -> list[AgentVersionResponse]:
    await _get_project(db, project_id)
    result = await db.execute(
        select(AgentVersion).where(AgentVersion.project_id == project_id).order_by(AgentVersion.created_at.desc())
    )
    return [_to_response(v) for v in result.scalars().all()]


async def create_version(db: AsyncSession, project_id: UUID, data: AgentVersionCreate) -> AgentVersionResponse:
    await _get_project(db, project_id)
    version = AgentVersion(project_id=project_id, **data.model_dump())
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return _to_response(version)


async def update_version(
    db: AsyncSession, project_id: UUID, version_id: UUID, data: AgentVersionUpdate
) -> AgentVersionResponse:
    version = await db.get(AgentVersion, version_id)
    if not version or version.project_id != project_id:
        raise HTTPException(404, detail="Agent version not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(version, key, value)

    await db.commit()
    await db.refresh(version)
    return _to_response(version)


async def delete_version(db: AsyncSession, project_id: UUID, version_id: UUID) -> None:
    version = await db.get(AgentVersion, version_id)
    if not version or version.project_id != project_id:
        raise HTTPException(404, detail="Agent version not found")

    await db.delete(version)
    await db.commit()


async def test_connection(db: AsyncSession, project_id: UUID, version_id: UUID) -> AgentTestResult:
    version = await db.get(AgentVersion, version_id)
    if not version or version.project_id != project_id:
        raise HTTPException(404, detail="Agent version not found")

    if not version.endpoint:
        raise HTTPException(400, detail="Agent endpoint not configured")

    try:
        client = AgentClient(version)
        reply, _ = await client.send_message("你好")
        version.connection_status = "success"
        await db.commit()
        return AgentTestResult(status="success", reply=reply)
    except Exception as e:
        version.connection_status = "failed"
        await db.commit()
        return AgentTestResult(status="failed", error=_sanitize_error(str(e)))
