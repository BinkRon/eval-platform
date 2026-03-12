from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TestCaseCreate(BaseModel):
    name: str = Field(max_length=100)
    sparring_prompt: str = Field(min_length=1)
    first_message: str | None = None
    max_rounds: int = Field(default=50, ge=3, le=100)
    sort_order: int = 0


class TestCaseUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    sparring_prompt: str | None = Field(default=None, min_length=1)
    first_message: str | None = None
    max_rounds: int | None = Field(default=None, ge=3, le=100)
    sort_order: int | None = None


class TestCaseResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    sparring_prompt: str
    first_message: str | None
    max_rounds: int
    sort_order: int
    last_result: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
