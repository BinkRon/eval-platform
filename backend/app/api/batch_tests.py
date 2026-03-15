import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_project_access
from app.models.batch_test import BatchTest
from app.models.project import Project
from app.schemas.batch_test import BatchTestCreate, BatchTestDetail, BatchTestProgress, BatchTestResponse
from app.services.batch_scheduler import run_batch_test
from app.services import batch_test_service

router = APIRouter(prefix="/api/projects/{project_id}/batch-tests", tags=["batch-tests"])

_background_tasks: set[asyncio.Task] = set()


@router.get("", response_model=list[BatchTestResponse])
async def list_batch_tests(project_id: UUID, db: AsyncSession = Depends(get_db), _: Project = Depends(verify_project_access)):
    """获取项目下所有批量测试记录。"""
    return await batch_test_service.list_batch_tests(db, project_id)


@router.post("", response_model=BatchTestResponse, status_code=201)
async def create_batch_test(project_id: UUID, data: BatchTestCreate, db: AsyncSession = Depends(get_db), _: Project = Depends(verify_project_access)):
    """发起新的批量测试，后台异步执行。"""
    batch = await batch_test_service.validate_and_create(db, project_id, data)
    await db.commit()
    await db.refresh(batch)

    # Start batch test in background (hold reference to prevent GC)
    task = asyncio.create_task(run_batch_test(batch.id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return batch


@router.delete("/{batch_id}", status_code=204)
async def delete_batch_test(project_id: UUID, batch_id: UUID, db: AsyncSession = Depends(get_db), _: Project = Depends(verify_project_access)):
    """删除指定批量测试记录及其所有用例结果。"""
    await batch_test_service.delete_batch_test(db, project_id, batch_id)


@router.get("/{batch_id}", response_model=BatchTestDetail)
async def get_batch_test(project_id: UUID, batch_id: UUID, db: AsyncSession = Depends(get_db), _: Project = Depends(verify_project_access)):
    """获取批量测试详情，包含所有用例结果。"""
    detail = await batch_test_service.get_batch_test_detail(db, project_id, batch_id)
    if not detail:
        raise HTTPException(404, detail="Batch test not found")
    return detail


@router.get("/{batch_id}/progress", response_model=BatchTestProgress)
async def get_batch_progress(project_id: UUID, batch_id: UUID, db: AsyncSession = Depends(get_db), _: Project = Depends(verify_project_access)):
    """查询批量测试的实时进度（前端轮询用）。"""
    batch = await db.get(BatchTest, batch_id)
    if not batch or batch.project_id != project_id:
        raise HTTPException(404, detail="Batch test not found")

    return BatchTestProgress(
        status=batch.status,
        total_cases=batch.total_cases,
        completed_cases=batch.completed_cases,
        passed_cases=batch.passed_cases,
    )
