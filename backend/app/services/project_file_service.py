import logging
import os
import pathlib
import uuid as uuid_mod
from uuid import UUID

import aiofiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import NotFoundError, ValidationError
from app.models.project import Project
from app.models.project_file import ProjectFile

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".xlsx", ".csv"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


async def _get_project(db: AsyncSession, project_id: UUID) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("项目不存在")
    return project


def _sanitize_filename(filename: str) -> str:
    """Strip path components to prevent path traversal attacks."""
    safe = pathlib.Path(filename).name
    if not safe or safe in (".", ".."):
        raise ValidationError("文件名非法")
    return safe


def _validate_file(filename: str, file_size: int) -> str:
    """Validate file type and size, return file extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"不支持的文件类型: {ext}，支持: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    if file_size > MAX_FILE_SIZE:
        raise ValidationError(f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）")
    return ext


async def upload_file(
    db: AsyncSession, project_id: UUID, filename: str, content: bytes
) -> ProjectFile:
    await _get_project(db, project_id)
    filename = _sanitize_filename(filename)
    ext = _validate_file(filename, len(content))

    # Build storage path: <FILE_STORAGE_PATH>/<project_id>/<uuid>.<ext>
    project_dir = os.path.join(settings.file_storage_path, str(project_id))
    os.makedirs(project_dir, exist_ok=True)
    storage_filename = f"{uuid_mod.uuid4()}{ext}"
    storage_path = os.path.join(project_dir, storage_filename)

    async with aiofiles.open(storage_path, "wb") as f:
        await f.write(content)

    pf = ProjectFile(
        project_id=project_id,
        filename=filename,
        file_type=ext.lstrip("."),
        file_size=len(content),
        storage_path=storage_path,
    )
    db.add(pf)
    await db.commit()
    await db.refresh(pf)
    return pf


async def list_files(db: AsyncSession, project_id: UUID) -> list[ProjectFile]:
    await _get_project(db, project_id)
    result = await db.execute(
        select(ProjectFile)
        .where(ProjectFile.project_id == project_id)
        .order_by(ProjectFile.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_file(db: AsyncSession, project_id: UUID, file_id: UUID) -> None:
    pf = await db.get(ProjectFile, file_id)
    if not pf or pf.project_id != project_id:
        raise NotFoundError("文件不存在")

    # DB first, then physical file — orphan files are easier to clean up than orphan records
    storage_path = pf.storage_path
    await db.delete(pf)
    await db.commit()

    try:
        os.remove(storage_path)
    except OSError as e:
        logger.warning(f"Failed to delete physical file {storage_path}: {e}")
