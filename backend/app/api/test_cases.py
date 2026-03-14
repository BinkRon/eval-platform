from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_project_access
from app.models.project import Project
from app.schemas.test_case import TestCaseCreate, TestCaseResponse, TestCaseUpdate
from app.services import test_case_service

router = APIRouter(prefix="/api/projects/{project_id}/test-cases", tags=["test-cases"])


@router.get("", response_model=list[TestCaseResponse])
async def list_test_cases(project_id: UUID, db: AsyncSession = Depends(get_db), _: Project = Depends(verify_project_access)):
    return await test_case_service.list_with_last_result(db, project_id)


@router.post("", response_model=TestCaseResponse, status_code=201)
async def create_test_case(project_id: UUID, data: TestCaseCreate, db: AsyncSession = Depends(get_db), _: Project = Depends(verify_project_access)):
    return await test_case_service.create_test_case(db, project_id, data)


@router.put("/{case_id}", response_model=TestCaseResponse)
async def update_test_case(project_id: UUID, case_id: UUID, data: TestCaseUpdate, db: AsyncSession = Depends(get_db), _: Project = Depends(verify_project_access)):
    return await test_case_service.update_test_case(db, project_id, case_id, data)


@router.delete("/{case_id}", status_code=204)
async def delete_test_case(project_id: UUID, case_id: UUID, db: AsyncSession = Depends(get_db), _: Project = Depends(verify_project_access)):
    await test_case_service.delete_test_case(db, project_id, case_id)
