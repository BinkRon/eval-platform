from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.agent_version import AgentVersion
from app.models.batch_test import BatchTest
from app.models.project import Project
from app.models.test_case import TestCase
from app.schemas.project import (
    LatestBatchSummary,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = list(result.scalars().all())

    if not projects:
        return []

    project_ids = [p.id for p in projects]

    # Batch count queries
    av_result = await db.execute(
        select(AgentVersion.project_id, func.count())
        .where(AgentVersion.project_id.in_(project_ids))
        .group_by(AgentVersion.project_id)
    )
    av_counts = dict(av_result.all())
    tc_result = await db.execute(
        select(TestCase.project_id, func.count())
        .where(TestCase.project_id.in_(project_ids))
        .group_by(TestCase.project_id)
    )
    tc_counts = dict(tc_result.all())
    bt_result = await db.execute(
        select(BatchTest.project_id, func.count())
        .where(BatchTest.project_id.in_(project_ids))
        .group_by(BatchTest.project_id)
    )
    bt_counts = dict(bt_result.all())

    # Latest 2 completed batches per project (for pass_rate + change)
    # Use ROW_NUMBER() window function to limit to 2 per project in DB
    row_num = (
        func.row_number()
        .over(partition_by=BatchTest.project_id, order_by=BatchTest.created_at.desc())
        .label("rn")
    )
    subq = (
        select(BatchTest.id, row_num)
        .where(
            BatchTest.project_id.in_(project_ids),
            BatchTest.status == "completed",
        )
        .subquery()
    )
    result = await db.execute(
        select(BatchTest)
        .join(subq, BatchTest.id == subq.c.id)
        .where(subq.c.rn <= 2)
        .order_by(BatchTest.project_id, BatchTest.created_at.desc())
        .options(selectinload(BatchTest.agent_version))
    )
    recent_batches: dict[UUID, list] = {}
    for bt in result.scalars().all():
        pid = bt.project_id
        if pid not in recent_batches:
            recent_batches[pid] = []
        recent_batches[pid].append(bt)

    # Build responses
    responses = []
    for p in projects:
        latest_batch = None
        batches = recent_batches.get(p.id, [])
        if batches:
            latest = batches[0]
            pass_rate = latest.passed_cases / latest.total_cases if latest.total_cases > 0 else 0.0

            pass_rate_change = None
            if len(batches) > 1:
                prev = batches[1]
                prev_total = prev.total_cases
                prev_rate = prev.passed_cases / prev_total if prev_total > 0 else 0.0
                pass_rate_change = round((pass_rate - prev_rate) * 100, 1)

            latest_batch = LatestBatchSummary(
                created_at=latest.created_at,
                agent_version_name=latest.agent_version.name if latest.agent_version else "已删除",
                pass_rate=round(pass_rate, 4),
                pass_rate_change=pass_rate_change,
            )

        responses.append(ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            created_at=p.created_at,
            updated_at=p.updated_at,
            agent_version_count=av_counts.get(p.id, 0),
            test_case_count=tc_counts.get(p.id, 0),
            batch_test_count=bt_counts.get(p.id, 0),
            latest_batch=latest_batch,
        ))

    return responses


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(name=data.name, description=data.description)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: UUID, data: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.commit()
    await db.refresh(project)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")

    await db.delete(project)
    await db.commit()
