import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.batch_test import BatchTest
from app.models.project import Project
from app.schemas.batch_test import BatchTestCreate, BatchTestDetail, BatchTestProgress, BatchTestResponse
from app.services.batch_scheduler import run_batch_test
from app.services import batch_test_service

router = APIRouter(prefix="/api/projects/{project_id}/batch-tests", tags=["batch-tests"])

_background_tasks: set[asyncio.Task] = set()


@router.get("", response_model=list[BatchTestResponse])
async def list_batch_tests(project_id: UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")

    result = await db.execute(
        select(BatchTest).where(BatchTest.project_id == project_id).order_by(BatchTest.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=BatchTestResponse, status_code=201)
async def create_batch_test(project_id: UUID, data: BatchTestCreate, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")

    batch = await batch_test_service.validate_and_create(db, project_id, data)
    await db.commit()
    await db.refresh(batch)

    # Start batch test in background (hold reference to prevent GC)
    task = asyncio.create_task(run_batch_test(batch.id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return batch


@router.get("/{batch_id}", response_model=BatchTestDetail)
async def get_batch_test(project_id: UUID, batch_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BatchTest)
        .where(BatchTest.id == batch_id, BatchTest.project_id == project_id)
        .options(selectinload(BatchTest.test_results))
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(404, detail="Batch test not found")
    return batch


@router.get("/{batch_id}/progress", response_model=BatchTestProgress)
async def get_batch_progress(project_id: UUID, batch_id: UUID, db: AsyncSession = Depends(get_db)):
    batch = await db.get(BatchTest, batch_id)
    if not batch or batch.project_id != project_id:
        raise HTTPException(404, detail="Batch test not found")

    return BatchTestProgress(
        status=batch.status,
        total_cases=batch.total_cases,
        completed_cases=batch.completed_cases,
        passed_cases=batch.passed_cases,
    )
