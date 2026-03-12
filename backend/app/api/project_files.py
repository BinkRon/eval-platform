from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import ValidationError
from app.schemas.project_file import ProjectFileResponse
from app.services import project_file_service
from app.services.project_file_service import MAX_FILE_SIZE

router = APIRouter(
    prefix="/api/projects/{project_id}/files", tags=["project-files"]
)


@router.get("", response_model=list[ProjectFileResponse])
async def list_files(project_id: UUID, db: AsyncSession = Depends(get_db)):
    return await project_file_service.list_files(db, project_id)


@router.post("", response_model=ProjectFileResponse, status_code=201)
async def upload_file(
    project_id: UUID,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise ValidationError("文件名不能为空")
    # Reject oversized files before reading full content into memory
    if file.size is not None and file.size > MAX_FILE_SIZE:
        raise ValidationError(f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）")
    content = await file.read()
    return await project_file_service.upload_file(db, project_id, file.filename, content)


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    project_id: UUID, file_id: UUID, db: AsyncSession = Depends(get_db)
):
    await project_file_service.delete_file(db, project_id, file_id)
