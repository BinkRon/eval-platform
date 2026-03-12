from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.judge_config import ChecklistItem, EvalDimension, JudgeConfig
from app.schemas.judge_config import JudgeConfigUpdate


async def save_judge_config(db: AsyncSession, project_id: UUID, data: JudgeConfigUpdate) -> JudgeConfig:
    """Create or replace judge config with all sub-entities in one transaction."""
    result = await db.execute(
        select(JudgeConfig)
        .where(JudgeConfig.project_id == project_id)
        .options(selectinload(JudgeConfig.checklist_items), selectinload(JudgeConfig.eval_dimensions))
    )
    config = result.scalar_one_or_none()

    if not config:
        config = JudgeConfig(project_id=project_id, pass_threshold=data.pass_threshold)
        db.add(config)
        await db.flush()
    else:
        config.pass_threshold = data.pass_threshold
        for item in list(config.checklist_items):
            await db.delete(item)
        for dim in list(config.eval_dimensions):
            await db.delete(dim)

    for item_data in data.checklist_items:
        db.add(ChecklistItem(
            judge_config_id=config.id,
            content=item_data.content,
            level=item_data.level,
            sort_order=item_data.sort_order,
        ))

    for dim_data in data.eval_dimensions:
        db.add(EvalDimension(
            judge_config_id=config.id,
            name=dim_data.name,
            judge_prompt_segment=dim_data.judge_prompt_segment,
            sort_order=dim_data.sort_order,
        ))

    await db.flush()
    return config
