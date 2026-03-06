from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TestCaseCreate(BaseModel):
    name: str = Field(max_length=100)
    first_message: str
    persona_background: str | None = None
    persona_behavior: str | None = None
    max_rounds: int = 20
    sort_order: int = 0


class TestCaseUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    first_message: str | None = None
    persona_background: str | None = None
    persona_behavior: str | None = None
    max_rounds: int | None = None
    sort_order: int | None = None


class TestCaseResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    first_message: str
    persona_background: str | None
    persona_behavior: str | None
    max_rounds: int
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
