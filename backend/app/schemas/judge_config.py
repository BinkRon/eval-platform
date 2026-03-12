from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChecklistItemData(BaseModel):
    id: UUID | None = None
    content: str
    level: Literal["must", "should"] = "must"
    sort_order: int = 0


class EvalDimensionData(BaseModel):
    id: UUID | None = None
    name: str = Field(max_length=100)
    judge_prompt_segment: str = Field(min_length=1)
    sort_order: int = 0


class JudgeConfigUpdate(BaseModel):
    pass_threshold: float = 2.0
    checklist_items: list[ChecklistItemData] = []
    eval_dimensions: list[EvalDimensionData] = []


class ChecklistItemResponse(BaseModel):
    id: UUID
    content: str
    level: str
    sort_order: int

    model_config = {"from_attributes": True}


class EvalDimensionResponse(BaseModel):
    id: UUID
    name: str
    judge_prompt_segment: str
    sort_order: int

    model_config = {"from_attributes": True}


class JudgeConfigResponse(BaseModel):
    id: UUID
    project_id: UUID
    pass_threshold: float
    checklist_items: list[ChecklistItemResponse]
    eval_dimensions: list[EvalDimensionResponse]

    model_config = {"from_attributes": True}
