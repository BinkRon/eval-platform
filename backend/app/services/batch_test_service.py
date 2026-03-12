from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import NotFoundError, ValidationError
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

    tc_query = select(TestCase).where(TestCase.project_id == project_id).order_by(TestCase.sort_order)
    if data.test_case_ids:
        tc_query = tc_query.where(TestCase.id.in_(data.test_case_ids))
    tc_result = await db.execute(tc_query)
    test_cases = list(tc_result.scalars().all())
    if data.test_case_ids and not test_cases:
        raise ValidationError("所选测试用例不存在或不属于当前项目")
    if not test_cases:
        raise ValidationError("请先添加测试用例")

    jc_result = await db.execute(
        select(JudgeConfig)
        .where(JudgeConfig.project_id == project_id)
        .options(selectinload(JudgeConfig.checklist_items), selectinload(JudgeConfig.eval_dimensions))
    )
    judge_config = jc_result.scalar_one_or_none()
    if not judge_config or (not judge_config.checklist_items and not judge_config.eval_dimensions):
        raise ValidationError("请先配置裁判标准（至少 1 条 Checklist 或 1 个评判维度）")

    # Filter checklist items and eval dimensions by provided IDs
    checklist_items = judge_config.checklist_items
    if data.checklist_item_ids:
        id_set = set(data.checklist_item_ids)
        checklist_items = [ci for ci in checklist_items if ci.id in id_set]

    eval_dimensions = judge_config.eval_dimensions
    if data.eval_dimension_ids:
        id_set = set(data.eval_dimension_ids)
        eval_dimensions = [ed for ed in eval_dimensions if ed.id in id_set]

    if data.checklist_item_ids and not checklist_items:
        raise ValidationError("所选 Checklist 检查项不属于当前项目")
    if data.eval_dimension_ids and not eval_dimensions:
        raise ValidationError("所选评判维度不属于当前项目")
    if not checklist_items and not eval_dimensions:
        raise ValidationError("至少需要选择 1 条 Checklist 或 1 个评判维度")

    pass_threshold = data.pass_threshold if data.pass_threshold is not None else float(judge_config.pass_threshold)

    mc_result = await db.execute(select(ModelConfig).where(ModelConfig.project_id == project_id))
    model_config = mc_result.scalar_one_or_none()
    if not model_config or not model_config.sparring_provider or not model_config.judge_provider:
        raise ValidationError("请先配置对练模型和裁判模型")

    # Freeze current experiment config as snapshot (with filtered selections)
    config_snapshot = {
        "agent_version": {
            "id": str(version.id),
            "name": version.name,
            "endpoint": version.endpoint,
        },
        "test_cases": [
            {
                "id": str(tc.id),
                "name": tc.name,
                "sparring_prompt": tc.sparring_prompt,
                "first_message": tc.first_message,
                "max_rounds": tc.max_rounds,
            }
            for tc in test_cases
        ],
        "judge_config": {
            "pass_threshold": pass_threshold,
            "checklist_items": [
                {"content": ci.content, "level": ci.level}
                for ci in checklist_items
            ],
            "eval_dimensions": [
                {
                    "name": ed.name,
                    "judge_prompt_segment": ed.judge_prompt_segment,
                }
                for ed in eval_dimensions
            ],
        },
        "model_config": {
            "sparring_provider": model_config.sparring_provider,
            "sparring_model": model_config.sparring_model,
            "judge_provider": model_config.judge_provider,
            "judge_model": model_config.judge_model,
        },
    }

    batch = BatchTest(
        project_id=project_id,
        agent_version_id=data.agent_version_id,
        concurrency=data.concurrency,
        status="pending",
        config_snapshot=config_snapshot,
    )
    db.add(batch)
    await db.flush()
    return batch


async def delete_batch_test(db: AsyncSession, project_id: UUID, batch_id: UUID) -> None:
    """Delete a batch test and its results. Running/pending batches cannot be deleted."""
    batch = await db.get(BatchTest, batch_id)
    if not batch or batch.project_id != project_id:
        raise NotFoundError("批测记录不存在")
    if batch.status in ("running", "pending"):
        raise ValidationError("运行中或等待中的批测不可删除")
    await db.delete(batch)
    await db.commit()


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
