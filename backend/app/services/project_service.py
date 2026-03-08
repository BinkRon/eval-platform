from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import NotFoundError
from app.models.agent_version import AgentVersion
from app.models.batch_test import BatchTest
from app.models.judge_config import ChecklistItem, EvalDimension, JudgeConfig
from app.models.model_config import ModelConfig
from app.models.project import Project
from app.models.test_case import TestCase
from app.schemas.project import (
    ConfigReadiness,
    ConfigReadinessItem,
    LatestBatchSummary,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)


async def list_projects(db: AsyncSession) -> list[ProjectResponse]:
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


async def create_project(db: AsyncSession, data: ProjectCreate) -> ProjectResponse:
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


async def get_project(db: AsyncSession, project_id: UUID) -> ProjectResponse:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project not found")
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


async def update_project(db: AsyncSession, project_id: UUID, data: ProjectUpdate) -> ProjectResponse:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project not found")

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


async def delete_project(db: AsyncSession, project_id: UUID) -> None:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project not found")

    await db.delete(project)
    await db.commit()


async def get_config_readiness(db: AsyncSession, project_id: UUID) -> ConfigReadiness:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project not found")

    # 1. Agent Version: at least 1 with connection_status == "success"
    av_result = await db.execute(
        select(func.count()).select_from(AgentVersion).where(
            AgentVersion.project_id == project_id,
            AgentVersion.connection_status == "success",
        )
    )
    av_success_count = av_result.scalar_one()
    agent_version = ConfigReadinessItem(
        ready=av_success_count > 0,
        message=f"{av_success_count} 个版本连接测试通过" if av_success_count > 0 else "无可用 Agent 版本（需至少 1 个连接测试通过）",
    )

    # 2. Test Cases: at least 1
    tc_result = await db.execute(
        select(func.count()).select_from(TestCase).where(TestCase.project_id == project_id)
    )
    tc_count = tc_result.scalar_one()
    test_case = ConfigReadinessItem(
        ready=tc_count > 0,
        message=f"{tc_count} 个测试用例" if tc_count > 0 else "无测试用例",
    )

    # 3. Judge Config: at least 1 ChecklistItem or 1 EvalDimension
    jc_result = await db.execute(
        select(JudgeConfig.id).where(JudgeConfig.project_id == project_id)
    )
    jc_id = jc_result.scalar_one_or_none()

    if jc_id:
        cl_result = await db.execute(
            select(func.count()).select_from(ChecklistItem).where(ChecklistItem.judge_config_id == jc_id)
        )
        cl_count = cl_result.scalar_one()
        ed_result = await db.execute(
            select(func.count()).select_from(EvalDimension).where(EvalDimension.judge_config_id == jc_id)
        )
        ed_count = ed_result.scalar_one()
    else:
        cl_count = 0
        ed_count = 0

    judge_ready = cl_count > 0 or ed_count > 0
    judge_config = ConfigReadinessItem(
        ready=judge_ready,
        message=f"{cl_count} 个检查项, {ed_count} 个评判维度" if judge_ready else "未配置裁判规则（需至少 1 个检查项或评判维度）",
    )

    # 4. Model Config: sparring + judge provider/model/system_prompt all set
    mc_result = await db.execute(
        select(ModelConfig).where(ModelConfig.project_id == project_id)
    )
    mc = mc_result.scalar_one_or_none()

    if mc:
        missing = []
        if not mc.sparring_provider or not mc.sparring_model:
            missing.append("对练模型")
        if not mc.sparring_system_prompt:
            missing.append("对练 System Prompt")
        if not mc.judge_provider or not mc.judge_model:
            missing.append("裁判模型")
        if not mc.judge_system_prompt:
            missing.append("裁判 System Prompt")
        model_ready = len(missing) == 0
        model_config_status = ConfigReadinessItem(
            ready=model_ready,
            message="模型配置完整" if model_ready else f"缺少: {', '.join(missing)}",
        )
    else:
        model_config_status = ConfigReadinessItem(ready=False, message="未配置模型")

    items = [agent_version, test_case, judge_config, model_config_status]
    return ConfigReadiness(
        agent_version=agent_version,
        test_case=test_case,
        judge_config=judge_config,
        model_config_status=model_config_status,
        all_ready=all(item.ready for item in items),
    )
