from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BatchTestCreate(BaseModel):
    agent_version_id: UUID
    concurrency: int = Field(default=3, ge=1, le=20)


class BatchTestResponse(BaseModel):
    id: UUID
    project_id: UUID
    agent_version_id: UUID | None
    status: str
    concurrency: int
    total_cases: int
    passed_cases: int
    completed_cases: int
    created_at: datetime
    completed_at: datetime | None

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
    status: str
    conversation: list[dict] | None
    termination_reason: str | None
    actual_rounds: int | None
    checklist_results: list[dict] | None
    eval_scores: list[dict] | None
    judge_summary: str | None
    passed: bool | None
    error_message: str | None

    model_config = {"from_attributes": True}


class BatchTestDetail(BatchTestResponse):
    test_results: list[TestResultResponse]
