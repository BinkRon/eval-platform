from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import NotFoundError
from app.models.batch_test import BatchTest
from app.models.project import Project
from app.models.test_case import TestCase
from app.schemas.test_case import TestCaseCreate, TestCaseResponse, TestCaseUpdate


async def _get_project(db: AsyncSession, project_id: UUID) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("项目不存在")
    return project


async def create_test_case(db: AsyncSession, project_id: UUID, data: TestCaseCreate) -> TestCase:
    await _get_project(db, project_id)
    tc = TestCase(project_id=project_id, **data.model_dump())
    db.add(tc)
    await db.commit()
    await db.refresh(tc)
    return tc


async def update_test_case(db: AsyncSession, project_id: UUID, case_id: UUID, data: TestCaseUpdate) -> TestCase:
    tc = await db.get(TestCase, case_id)
    if not tc or tc.project_id != project_id:
        raise NotFoundError("测试用例不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tc, key, value)
    await db.commit()
    await db.refresh(tc)
    return tc


async def delete_test_case(db: AsyncSession, project_id: UUID, case_id: UUID) -> None:
    tc = await db.get(TestCase, case_id)
    if not tc or tc.project_id != project_id:
        raise NotFoundError("测试用例不存在")
    await db.delete(tc)
    await db.commit()


async def list_with_last_result(db: AsyncSession, project_id: UUID) -> list[TestCaseResponse]:
    """List test cases with last batch test result."""
    await _get_project(db, project_id)
    tc_result = await db.execute(
        select(TestCase)
        .where(TestCase.project_id == project_id)
        .order_by(TestCase.sort_order)
    )
    test_cases = tc_result.scalars().all()

    # Find the most recent completed batch test
    latest_batch_result = await db.execute(
        select(BatchTest)
        .where(BatchTest.project_id == project_id, BatchTest.status == "completed")
        .order_by(BatchTest.created_at.desc())
        .limit(1)
        .options(selectinload(BatchTest.test_results))
    )
    latest_batch = latest_batch_result.scalar_one_or_none()

    result_map: dict[UUID, str] = {}
    if latest_batch:
        for tr in latest_batch.test_results:
            if tr.test_case_id and tr.status == "completed":
                result_map[tr.test_case_id] = "passed" if tr.passed else "failed"

    return [
        TestCaseResponse(
            **{k: getattr(tc, k) for k in TestCaseResponse.model_fields if k != 'last_result'},
            last_result=result_map.get(tc.id),
        )
        for tc in test_cases
    ]
