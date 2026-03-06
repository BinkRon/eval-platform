from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class LatestBatchSummary(BaseModel):
    created_at: datetime
    agent_version_name: str
    pass_rate: float
    pass_rate_change: float | None = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    agent_version_count: int = 0
    test_case_count: int = 0
    batch_test_count: int = 0
    latest_batch: LatestBatchSummary | None = None

    model_config = {"from_attributes": True}
