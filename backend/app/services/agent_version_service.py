from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError, ValidationError
from app.models.agent_version import AgentVersion
from app.models.project import Project
from app.schemas.agent_version import (
    AgentTestResult,
    AgentVersionCreate,
    AgentVersionResponse,
    AgentVersionUpdate,
)
from app.services.agent_client import AgentClient
from app.utils.crypto import decrypt, encrypt
from app.utils.error_sanitizer import sanitize_error


def _to_response(v: AgentVersion) -> AgentVersionResponse:
    data = {c.key: getattr(v, c.key) for c in AgentVersion.__table__.columns if c.key != "auth_token"}
    data["auth_token_set"] = bool(v.auth_token)
    return AgentVersionResponse(**data)


async def _get_project(db: AsyncSession, project_id: UUID) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project not found")
    return project


async def list_versions(db: AsyncSession, project_id: UUID) -> list[AgentVersionResponse]:
    await _get_project(db, project_id)
    result = await db.execute(
        select(AgentVersion).where(AgentVersion.project_id == project_id).order_by(AgentVersion.created_at.desc())
    )
    return [_to_response(v) for v in result.scalars().all()]


async def create_version(db: AsyncSession, project_id: UUID, data: AgentVersionCreate) -> AgentVersionResponse:
    await _get_project(db, project_id)
    dump = data.model_dump()
    if dump.get("auth_token"):
        dump["auth_token"] = encrypt(dump["auth_token"])
    version = AgentVersion(project_id=project_id, **dump)
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return _to_response(version)


async def update_version(
    db: AsyncSession, project_id: UUID, version_id: UUID, data: AgentVersionUpdate
) -> AgentVersionResponse:
    version = await db.get(AgentVersion, version_id)
    if not version or version.project_id != project_id:
        raise NotFoundError("Agent version not found")

    update_data = data.model_dump(exclude_unset=True)
    # 空 token 表示不修改，跳过更新
    if "auth_token" in update_data and not update_data["auth_token"]:
        del update_data["auth_token"]
    elif "auth_token" in update_data and update_data["auth_token"]:
        update_data["auth_token"] = encrypt(update_data["auth_token"])
    for key, value in update_data.items():
        setattr(version, key, value)

    await db.commit()
    await db.refresh(version)
    return _to_response(version)


async def delete_version(db: AsyncSession, project_id: UUID, version_id: UUID) -> None:
    version = await db.get(AgentVersion, version_id)
    if not version or version.project_id != project_id:
        raise NotFoundError("Agent version not found")

    await db.delete(version)
    await db.commit()


async def test_connection(db: AsyncSession, project_id: UUID, version_id: UUID) -> AgentTestResult:
    version = await db.get(AgentVersion, version_id)
    if not version or version.project_id != project_id:
        raise NotFoundError("Agent version not found")

    if not version.endpoint:
        raise ValidationError("Agent endpoint not configured")

    try:
        # Decrypt auth_token into a detached copy to avoid writing plaintext back to DB
        decrypted_token = decrypt(version.auth_token) if version.auth_token else None
        # Use SimpleNamespace as a lightweight proxy for AgentClient
        from types import SimpleNamespace
        agent_proxy = SimpleNamespace(**{c.key: getattr(version, c.key) for c in AgentVersion.__table__.columns})
        agent_proxy.auth_token = decrypted_token

        client = AgentClient(agent_proxy)
        reply, _ = await client.send_message("你好")
        version.connection_status = "success"
        await db.commit()
        return AgentTestResult(status="success", reply=reply)
    except Exception as e:
        version.connection_status = "failed"
        await db.commit()
        return AgentTestResult(status="failed", error=sanitize_error(str(e)))


async def test_connection_unsaved(data: AgentVersionCreate) -> AgentTestResult:
    if not data.endpoint:
        raise ValidationError("Agent endpoint not configured")

    try:
        from types import SimpleNamespace
        agent_proxy = SimpleNamespace(**data.model_dump())
        client = AgentClient(agent_proxy)
        reply, _ = await client.send_message("你好")
        return AgentTestResult(status="success", reply=reply)
    except Exception as e:
        return AgentTestResult(status="failed", error=sanitize_error(str(e)))
