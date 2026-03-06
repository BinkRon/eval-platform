from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent_version import AgentVersion
from app.models.batch_test import BatchTest
from app.models.judge_config import JudgeConfig
from app.models.model_config import ModelConfig
from app.models.test_case import TestCase
from app.schemas.batch_test import BatchTestCreate


async def validate_and_create(db: AsyncSession, project_id: UUID, data: BatchTestCreate) -> BatchTest:
    """Validate pre-conditions and create a batch test record."""
    version = await db.get(AgentVersion, data.agent_version_id)
    if not version or version.project_id != project_id:
        raise HTTPException(400, detail="Agent 版本不存在")
    if not version.endpoint:
        raise HTTPException(400, detail="请先配置 Agent 版本的 API Endpoint")

    tc_result = await db.execute(select(TestCase).where(TestCase.project_id == project_id).limit(1))
    if not tc_result.scalar_one_or_none():
        raise HTTPException(400, detail="请先添加测试用例")

    jc_result = await db.execute(
        select(JudgeConfig)
        .where(JudgeConfig.project_id == project_id)
        .options(selectinload(JudgeConfig.checklist_items), selectinload(JudgeConfig.eval_dimensions))
    )
    judge_config = jc_result.scalar_one_or_none()
    if not judge_config or (not judge_config.checklist_items and not judge_config.eval_dimensions):
        raise HTTPException(400, detail="请先配置裁判标准（至少 1 条 Checklist 或 1 个评判维度）")

    mc_result = await db.execute(select(ModelConfig).where(ModelConfig.project_id == project_id))
    model_config = mc_result.scalar_one_or_none()
    if not model_config or not model_config.sparring_provider or not model_config.judge_provider:
        raise HTTPException(400, detail="请先配置对练模型和裁判模型")

    batch = BatchTest(
        project_id=project_id,
        agent_version_id=data.agent_version_id,
        concurrency=data.concurrency,
        status="pending",
    )
    db.add(batch)
    await db.flush()
    return batch
