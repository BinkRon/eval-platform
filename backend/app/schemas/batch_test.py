from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BatchTestCreate(BaseModel):
    agent_version_id: UUID
    concurrency: int = Field(default=3, ge=1, le=20)
    test_case_ids: list[UUID] | None = None
    checklist_item_ids: list[UUID] | None = None
    eval_dimension_ids: list[UUID] | None = None
    pass_threshold: float | None = Field(default=None, ge=1.0, le=3.0)


class BatchTestResponse(BaseModel):
    id: UUID
    project_id: UUID
    agent_version_id: UUID | None
    agent_version_name: str | None = None
    status: str
    concurrency: int
    total_cases: int
    passed_cases: int
    completed_cases: int
    created_at: datetime
    completed_at: datetime | None
    config_snapshot: dict | None = None

    model_config = {"from_attributes": True}


class BatchTestProgress(BaseModel):
    status: str
    total_cases: int
    completed_cases: int
    passed_cases: int


class TestResultResponse(BaseModel):
    id: UUID
    batch_test_id: UUID
    test_case_id: UUID | None
    test_case_name: str | None = None
    status: str
    conversation: list[dict] | None
    termination_reason: str | None
    actual_rounds: int | None
    checklist_results: list[dict] | None
    eval_scores: list[dict] | None
    judge_summary: str | None
    passed: bool | None
    error_message: str | None
    sparring_prompt_snapshot: str | None = None
    judge_prompt_snapshot: str | None = None

    model_config = {"from_attributes": True}


class BatchTestDetail(BatchTestResponse):
    test_results: list[TestResultResponse]
