import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.llm.factory import create_llm_adapter
from app.models.agent_version import AgentVersion
from app.models.batch_test import BatchTest, TestResult
from app.models.judge_config import JudgeConfig
from app.models.model_config import ModelConfig
from app.models.provider_config import ProviderConfig
from app.models.test_case import TestCase
from app.services.agent_client import AgentClient
from app.services.judge_runner import JudgeRunner
from app.services.sparring_runner import SparringRunner
from app.utils.error_sanitizer import sanitize_error

logger = logging.getLogger(__name__)


@dataclass
class BatchContext:
    agent_version: AgentVersion
    test_cases: list[TestCase]
    judge_config: JudgeConfig | None
    sparring_provider_name: str
    sparring_api_key: str
    sparring_model: str | None
    sparring_base_url: str | None
    sparring_system_prompt: str
    judge_provider_name: str
    judge_api_key: str
    judge_model: str | None
    judge_base_url: str | None
    judge_system_prompt: str
    pass_threshold: Decimal
    concurrency: int
    sparring_temperature: float | None
    sparring_max_tokens: int | None
    judge_temperature: float | None
    judge_max_tokens: int | None


async def run_batch_test(batch_test_id: UUID):
    async with async_session() as db:
        batch = await db.get(BatchTest, batch_test_id)
        if not batch:
            return
        batch.status = "running"
        await db.commit()

    try:
        await _execute_batch(batch_test_id)
    except (Exception, asyncio.CancelledError) as e:
        is_cancelled = isinstance(e, asyncio.CancelledError)
        logger.exception(f"Batch test {batch_test_id} failed: {e}")
        async with async_session() as db:
            batch = await db.get(BatchTest, batch_test_id)
            if batch:
                batch.status = "failed"
                batch.completed_at = datetime.utcnow()
                await db.commit()
        if is_cancelled:
            raise


async def _load_context(db: AsyncSession, batch: BatchTest) -> BatchContext | None:
    agent_version = await db.get(AgentVersion, batch.agent_version_id)
    if not agent_version:
        return None

    result = await db.execute(
        select(TestCase).where(TestCase.project_id == batch.project_id).order_by(TestCase.sort_order)
    )
    test_cases = list(result.scalars().all())

    result = await db.execute(
        select(JudgeConfig)
        .where(JudgeConfig.project_id == batch.project_id)
        .options(selectinload(JudgeConfig.checklist_items), selectinload(JudgeConfig.eval_dimensions))
    )
    judge_config = result.scalar_one_or_none()

    result = await db.execute(select(ModelConfig).where(ModelConfig.project_id == batch.project_id))
    model_config = result.scalar_one_or_none()
    if not model_config:
        return None

    if not model_config.sparring_model or not model_config.judge_model:
        logger.error("Sparring or judge model not configured")
        return None

    providers: dict[str, ProviderConfig] = {}
    result = await db.execute(select(ProviderConfig).where(ProviderConfig.is_active.is_(True)))
    for p in result.scalars().all():
        providers[p.provider_name] = p

    sparring_p = providers.get(model_config.sparring_provider)
    judge_p = providers.get(model_config.judge_provider)
    if not sparring_p or not judge_p:
        return None

    if not sparring_p.api_key or not judge_p.api_key:
        logger.error("Provider API key not configured for sparring or judge")
        return None

    return BatchContext(
        agent_version=agent_version,
        test_cases=test_cases,
        judge_config=judge_config,
        sparring_provider_name=model_config.sparring_provider,
        sparring_api_key=sparring_p.api_key,
        sparring_model=model_config.sparring_model,
        sparring_base_url=sparring_p.base_url,
        sparring_system_prompt=model_config.sparring_system_prompt or "",
        judge_provider_name=model_config.judge_provider,
        judge_api_key=judge_p.api_key,
        judge_model=model_config.judge_model,
        judge_base_url=judge_p.base_url,
        judge_system_prompt=model_config.judge_system_prompt or "",
        pass_threshold=judge_config.pass_threshold if judge_config else Decimal("2.0"),
        concurrency=batch.concurrency or 3,
        sparring_temperature=float(model_config.sparring_temperature) if model_config.sparring_temperature is not None else None,
        sparring_max_tokens=model_config.sparring_max_tokens,
        judge_temperature=float(model_config.judge_temperature) if model_config.judge_temperature is not None else None,
        judge_max_tokens=model_config.judge_max_tokens,
    )


async def _load_batch_context(batch_test_id: UUID) -> BatchContext | None:
    """Load a batch test and its context from DB. Returns None if not found or misconfigured."""
    async with async_session() as db:
        batch = await db.get(BatchTest, batch_test_id)
        if not batch:
            logger.error(f"BatchTest {batch_test_id} not found")
            return None
        ctx = await _load_context(db, batch)
        if not ctx:
            batch.status = "failed"
            batch.completed_at = datetime.utcnow()
            await db.commit()
            return None
    return ctx


async def _create_result_placeholders(batch_test_id: UUID, ctx: BatchContext):
    """Create pending TestResult rows for each test case."""
    async with async_session() as db:
        batch = await db.get(BatchTest, batch_test_id)
        for tc in ctx.test_cases:
            tr = TestResult(batch_test_id=batch.id, test_case_id=tc.id, status="pending")
            db.add(tr)
        batch.total_cases = len(ctx.test_cases)
        await db.commit()


def _setup_llm_clients(ctx: BatchContext) -> tuple:
    """Create sparring and judge LLM adapters from context."""
    sparring_llm = create_llm_adapter(
        ctx.sparring_provider_name, ctx.sparring_api_key, ctx.sparring_model, ctx.sparring_base_url
    )
    judge_llm = create_llm_adapter(
        ctx.judge_provider_name, ctx.judge_api_key, ctx.judge_model, ctx.judge_base_url
    )
    return sparring_llm, judge_llm


async def _run_all_cases(batch_test_id: UUID, ctx: BatchContext, sparring_llm, judge_llm):
    """Run all test cases concurrently with a semaphore limit."""
    semaphore = asyncio.Semaphore(ctx.concurrency)

    async def run_single_case(test_case: TestCase):
        async with semaphore:
            await _run_single_test(batch_test_id, test_case, ctx, sparring_llm, judge_llm)

    results = await asyncio.gather(*[run_single_case(tc) for tc in ctx.test_cases], return_exceptions=True)
    for r in results:
        if isinstance(r, BaseException):
            logger.error(f"Unexpected exception in run_single_case: {r}")


async def _finalize_batch(batch_test_id: UUID):
    """Compute final stats and mark batch as completed or failed."""
    try:
        async with async_session() as db:
            batch = await db.get(BatchTest, batch_test_id)
            result = await db.execute(select(TestResult).where(TestResult.batch_test_id == batch_test_id))
            results = list(result.scalars().all())
            completed_results = [r for r in results if r.status == "completed"]
            failed_results = [r for r in results if r.status == "failed"]
            batch.completed_cases = len(completed_results) + len(failed_results)
            batch.passed_cases = len([r for r in completed_results if r.passed is True])
            if len(completed_results) == 0 and len(failed_results) > 0:
                batch.status = "failed"
            else:
                batch.status = "completed"
            batch.completed_at = datetime.utcnow()
            await db.commit()
    except Exception as e:
        logger.exception(f"Failed to finalize batch test {batch_test_id}: {e}")


async def _execute_batch(batch_test_id: UUID):
    """Orchestrate a complete batch test execution."""
    ctx = await _load_batch_context(batch_test_id)
    if not ctx:
        return
    await _create_result_placeholders(batch_test_id, ctx)
    sparring_llm, judge_llm = _setup_llm_clients(ctx)
    await _run_all_cases(batch_test_id, ctx, sparring_llm, judge_llm)
    await _finalize_batch(batch_test_id)


async def _save_failed_result(
    batch_test_id: UUID,
    test_case_id: UUID,
    error_message: str,
    conversation: list[dict] | None = None,
    termination_reason: str | None = None,
    actual_rounds: int | None = None,
):
    """Save a failed test result and increment the completed counter."""
    async with async_session() as db:
        result = await db.execute(
            select(TestResult).where(
                TestResult.batch_test_id == batch_test_id,
                TestResult.test_case_id == test_case_id,
            )
        )
        tr = result.scalar_one()
        tr.status = "failed"
        tr.error_message = error_message
        tr.conversation = conversation
        tr.termination_reason = termination_reason
        tr.actual_rounds = actual_rounds
        await db.execute(
            update(BatchTest)
            .where(BatchTest.id == batch_test_id)
            .values(completed_cases=BatchTest.completed_cases + 1)
        )
        await db.commit()


async def _run_single_test(batch_test_id, test_case, ctx: BatchContext, sparring_llm, judge_llm):
    async with async_session() as db:
        result = await db.execute(
            select(TestResult).where(
                TestResult.batch_test_id == batch_test_id,
                TestResult.test_case_id == test_case.id,
            )
        )
        test_result = result.scalar_one()
        test_result.status = "running"
        await db.commit()

    # Phase 1: Sparring (对练)
    try:
        agent_client = AgentClient(ctx.agent_version)
        sparring_runner = SparringRunner(
            agent_client=agent_client,
            llm=sparring_llm,
            test_case=test_case,
            system_prompt=ctx.sparring_system_prompt,
            temperature=ctx.sparring_temperature,
            max_tokens=ctx.sparring_max_tokens,
        )
        conversation, termination_reason, actual_rounds = await sparring_runner.run()
    except Exception as e:
        logger.exception(f"Test case {test_case.id} sparring failed: {e}")
        await _save_failed_result(batch_test_id, test_case.id, sanitize_error(f"对练失败: {e}"))
        return

    # Phase 2: Judge (裁判)
    passed = True
    checklist_results = None
    eval_scores = None
    judge_summary = None

    try:
        if ctx.judge_config:
            judge_runner = JudgeRunner(
                llm=judge_llm,
                system_prompt=ctx.judge_system_prompt,
                checklist_items=ctx.judge_config.checklist_items,
                eval_dimensions=ctx.judge_config.eval_dimensions,
                pass_threshold=ctx.pass_threshold,
                temperature=ctx.judge_temperature,
                max_tokens=ctx.judge_max_tokens,
            )
            judge_result = await judge_runner.judge(conversation)
            checklist_results = judge_result.checklist_results
            eval_scores = judge_result.eval_scores
            judge_summary = judge_result.summary
            passed = judge_result.passed
    except Exception as e:
        logger.exception(f"Test case {test_case.id} judge failed: {e}")
        await _save_failed_result(
            batch_test_id, test_case.id, sanitize_error(f"评判失败: {e}"),
            conversation=conversation,
            termination_reason=termination_reason,
            actual_rounds=actual_rounds,
        )
        return

    # Save successful results + update progress in one transaction
    async with async_session() as db:
        result = await db.execute(
            select(TestResult).where(
                TestResult.batch_test_id == batch_test_id,
                TestResult.test_case_id == test_case.id,
            )
        )
        tr = result.scalar_one()
        tr.status = "completed"
        tr.conversation = conversation
        tr.termination_reason = termination_reason
        tr.actual_rounds = actual_rounds
        tr.checklist_results = checklist_results
        tr.eval_scores = eval_scores
        tr.judge_summary = judge_summary
        tr.passed = passed
        progress_values = {"completed_cases": BatchTest.completed_cases + 1}
        if passed:
            progress_values["passed_cases"] = BatchTest.passed_cases + 1
        await db.execute(
            update(BatchTest)
            .where(BatchTest.id == batch_test_id)
            .values(**progress_values)
        )
        await db.commit()
