from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import ValidationError
from app.models.agent_version import AgentVersion
from app.models.batch_test import BatchTest, TestResult
from app.models.judge_config import JudgeConfig
from app.models.model_config import ModelConfig
from app.models.test_case import TestCase
from app.schemas.batch_test import BatchTestCreate, BatchTestDetail, BatchTestResponse, TestResultResponse


async def validate_and_create(db: AsyncSession, project_id: UUID, data: BatchTestCreate) -> BatchTest:
    """Validate pre-conditions and create a batch test record."""
    version = await db.get(AgentVersion, data.agent_version_id)
    if not version or version.project_id != project_id:
        raise ValidationError("Agent 版本不存在")
    if not version.endpoint:
        raise ValidationError("请先配置 Agent 版本的 API Endpoint")
    if version.connection_status != "success":
        raise ValidationError("请先完成 Agent 版本的连接测试")

    tc_result = await db.execute(select(TestCase).where(TestCase.project_id == project_id).limit(1))
    if not tc_result.scalar_one_or_none():
        raise ValidationError("请先添加测试用例")

    jc_result = await db.execute(
        select(JudgeConfig)
        .where(JudgeConfig.project_id == project_id)
        .options(selectinload(JudgeConfig.checklist_items), selectinload(JudgeConfig.eval_dimensions))
    )
    judge_config = jc_result.scalar_one_or_none()
    if not judge_config or (not judge_config.checklist_items and not judge_config.eval_dimensions):
        raise ValidationError("请先配置裁判标准（至少 1 条 Checklist 或 1 个评判维度）")

    mc_result = await db.execute(select(ModelConfig).where(ModelConfig.project_id == project_id))
    model_config = mc_result.scalar_one_or_none()
    if not model_config or not model_config.sparring_provider or not model_config.judge_provider:
        raise ValidationError("请先配置对练模型和裁判模型")

    batch = BatchTest(
        project_id=project_id,
        agent_version_id=data.agent_version_id,
        concurrency=data.concurrency,
        status="pending",
    )
    db.add(batch)
    await db.flush()
    return batch


async def list_batch_tests(db: AsyncSession, project_id: UUID) -> list[BatchTestResponse]:
    """List batch tests with agent version name."""
    result = await db.execute(
        select(BatchTest)
        .where(BatchTest.project_id == project_id)
        .order_by(BatchTest.created_at.desc())
        .options(selectinload(BatchTest.agent_version))
    )
    batches = result.scalars().all()
    return [
        BatchTestResponse(
            **{k: getattr(b, k) for k in BatchTestResponse.model_fields if k != 'agent_version_name'},
            agent_version_name=b.agent_version.name if b.agent_version else None,
        )
        for b in batches
    ]


async def get_batch_test_detail(db: AsyncSession, project_id: UUID, batch_id: UUID) -> BatchTestDetail | None:
    """Get batch test detail with agent version name and test case names."""
    result = await db.execute(
        select(BatchTest)
        .where(BatchTest.id == batch_id, BatchTest.project_id == project_id)
        .options(
            selectinload(BatchTest.agent_version),
            selectinload(BatchTest.test_results).selectinload(TestResult.test_case),
        )
    )
    batch = result.scalar_one_or_none()
    if not batch:
        return None

    test_results = [
        TestResultResponse(
            **{k: getattr(tr, k) for k in TestResultResponse.model_fields if k != 'test_case_name'},
            test_case_name=tr.test_case.name if tr.test_case else None,
        )
        for tr in batch.test_results
    ]

    return BatchTestDetail(
        **{k: getattr(batch, k) for k in BatchTestResponse.model_fields if k != 'agent_version_name'},
        agent_version_name=batch.agent_version.name if batch.agent_version else None,
        test_results=test_results,
    )
