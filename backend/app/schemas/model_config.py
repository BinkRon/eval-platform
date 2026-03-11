from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _strip_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class ModelConfigUpdate(BaseModel):
    sparring_provider: str | None = Field(default=None, max_length=50)
    sparring_model: str | None = Field(default=None, max_length=100)
    sparring_temperature: Decimal | None = None
    sparring_max_tokens: int | None = Field(default=None, ge=1, le=32768)
    sparring_system_prompt: str | None = None
    judge_provider: str | None = Field(default=None, max_length=50)
    judge_model: str | None = Field(default=None, max_length=100)
    judge_temperature: Decimal | None = None
    judge_max_tokens: int | None = Field(default=None, ge=1, le=32768)
    judge_system_prompt: str | None = None

    @field_validator("sparring_provider", "sparring_model", "judge_provider", "judge_model", mode="before")
    @classmethod
    def strip_model_fields(cls, value: str | None) -> str | None:
        return _strip_optional_string(value)


class ModelConfigResponse(BaseModel):
    id: UUID
    project_id: UUID
    sparring_provider: str | None
    sparring_model: str | None
    sparring_temperature: Decimal | None
    sparring_max_tokens: int | None
    sparring_system_prompt: str | None
    judge_provider: str | None
    judge_model: str | None
    judge_temperature: Decimal | None
    judge_max_tokens: int | None
    judge_system_prompt: str | None

    model_config = {"from_attributes": True}
