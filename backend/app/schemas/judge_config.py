"""裁判配置相关的请求/响应模型。"""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChecklistItemData(BaseModel):
    """Checklist 检查项（创建/更新用）。"""

    id: UUID | None = Field(default=None, description="检查项 ID（更新时传入）")
    content: str = Field(description="检查项内容", examples=["Agent 必须在首轮回复中确认用户意图"])
    level: Literal["must", "should"] = Field(default="must", description="重要性级别。must: 必须通过；should: 建议通过")
    sort_order: int = Field(default=0, description="排序序号")


class EvalDimensionData(BaseModel):
    """评判维度（创建/更新用）。"""

    id: UUID | None = Field(default=None, description="维度 ID（更新时传入）")
    name: str = Field(max_length=100, description="维度名称", examples=["专业性"])
    judge_prompt_segment: str = Field(min_length=1, description="该维度的裁判 Prompt 片段，指导裁判如何评分")
    sort_order: int = Field(default=0, description="排序序号")


class JudgeConfigUpdate(BaseModel):
    """更新裁判配置（整体替换）。"""

    pass_threshold: float = Field(default=2.0, description="及格阈值，维度平均分 >= 此值判定通过", examples=[2.0])
    checklist_items: list[ChecklistItemData] = Field(default=[], description="Checklist 检查项列表")
    eval_dimensions: list[EvalDimensionData] = Field(default=[], description="评判维度列表")


class ChecklistItemResponse(BaseModel):
    """Checklist 检查项详情。"""

    id: UUID = Field(description="检查项 ID")
    content: str = Field(description="检查项内容")
    level: str = Field(description="重要性级别")
    sort_order: int = Field(description="排序序号")

    model_config = {"from_attributes": True}


class EvalDimensionResponse(BaseModel):
    """评判维度详情。"""

    id: UUID = Field(description="维度 ID")
    name: str = Field(description="维度名称")
    judge_prompt_segment: str = Field(description="裁判 Prompt 片段")
    sort_order: int = Field(description="排序序号")

    model_config = {"from_attributes": True}


class JudgeConfigResponse(BaseModel):
    """裁判配置详情。"""

    id: UUID = Field(description="配置 ID")
    project_id: UUID = Field(description="所属项目 ID")
    pass_threshold: float = Field(description="及格阈值")
    checklist_items: list[ChecklistItemResponse] = Field(description="Checklist 检查项")
    eval_dimensions: list[EvalDimensionResponse] = Field(description="评判维度")

    model_config = {"from_attributes": True}
