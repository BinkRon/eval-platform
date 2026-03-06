from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.batch_test import BatchTest
from app.models.test_case import TestCase
from app.schemas.test_case import TestCaseResponse


async def list_with_last_result(db: AsyncSession, project_id: UUID) -> list[TestCaseResponse]:
    """List test cases with last batch test result."""
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
