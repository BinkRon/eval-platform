from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import Project
from app.models.test_case import TestCase
from app.schemas.test_case import TestCaseCreate, TestCaseResponse, TestCaseUpdate

router = APIRouter(prefix="/api/projects/{project_id}/test-cases", tags=["test-cases"])


async def _get_project(project_id: UUID, db: AsyncSession) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, detail="Project not found")
    return project


@router.get("/", response_model=list[TestCaseResponse])
async def list_test_cases(project_id: UUID, db: AsyncSession = Depends(get_db)):
    await _get_project(project_id, db)
    result = await db.execute(
        select(TestCase).where(TestCase.project_id == project_id).order_by(TestCase.sort_order)
    )
    return result.scalars().all()


@router.post("/", response_model=TestCaseResponse, status_code=201)
async def create_test_case(project_id: UUID, data: TestCaseCreate, db: AsyncSession = Depends(get_db)):
    await _get_project(project_id, db)
    tc = TestCase(project_id=project_id, **data.model_dump())
    db.add(tc)
    await db.commit()
    return tc


@router.put("/{case_id}", response_model=TestCaseResponse)
async def update_test_case(project_id: UUID, case_id: UUID, data: TestCaseUpdate, db: AsyncSession = Depends(get_db)):
    tc = await db.get(TestCase, case_id)
    if not tc or tc.project_id != project_id:
        raise HTTPException(404, detail="Test case not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tc, key, value)

    await db.commit()
    return tc


@router.delete("/{case_id}", status_code=204)
async def delete_test_case(project_id: UUID, case_id: UUID, db: AsyncSession = Depends(get_db)):
    tc = await db.get(TestCase, case_id)
    if not tc or tc.project_id != project_id:
        raise HTTPException(404, detail="Test case not found")

    await db.delete(tc)
    await db.commit()
