"""模型配置相关的请求/响应模型。"""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _strip_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class ModelConfigUpdate(BaseModel):
    """更新模型配置（对练机器人 + 裁判机器人）。"""

    sparring_provider: str | None = Field(default=None, max_length=50, description="对练机器人供应商", examples=["openai"])
    sparring_model: str | None = Field(default=None, max_length=100, description="对练机器人模型", examples=["gpt-4o"])
    sparring_temperature: Decimal | None = Field(default=None, description="对练机器人温度", examples=[0.7])
    sparring_max_tokens: int | None = Field(default=None, ge=1, le=32768, description="对练机器人最大 Token 数")
    sparring_system_prompt: str | None = Field(default=None, description="对练机器人 System Prompt（空值使用默认）")
    judge_provider: str | None = Field(default=None, max_length=50, description="裁判机器人供应商")
    judge_model: str | None = Field(default=None, max_length=100, description="裁判机器人模型")
    judge_temperature: Decimal | None = Field(default=None, description="裁判机器人温度")
    judge_max_tokens: int | None = Field(default=None, ge=1, le=32768, description="裁判机器人最大 Token 数")
    judge_system_prompt: str | None = Field(default=None, description="裁判机器人 System Prompt（空值使用默认）")

    @field_validator("sparring_provider", "sparring_model", "judge_provider", "judge_model", mode="before")
    @classmethod
    def strip_model_fields(cls, value: str | None) -> str | None:
        return _strip_optional_string(value)


class ModelConfigResponse(BaseModel):
    """模型配置详情。"""

    id: UUID = Field(description="配置 ID")
    project_id: UUID = Field(description="所属项目 ID")
    sparring_provider: str | None = Field(description="对练机器人供应商")
    sparring_model: str | None = Field(description="对练机器人模型")
    sparring_temperature: Decimal | None = Field(description="对练机器人温度")
    sparring_max_tokens: int | None = Field(description="对练机器人最大 Token 数")
    sparring_system_prompt: str | None = Field(description="对练机器人 System Prompt")
    judge_provider: str | None = Field(description="裁判机器人供应商")
    judge_model: str | None = Field(description="裁判机器人模型")
    judge_temperature: Decimal | None = Field(description="裁判机器人温度")
    judge_max_tokens: int | None = Field(description="裁判机器人最大 Token 数")
    judge_system_prompt: str | None = Field(description="裁判机器人 System Prompt")

    model_config = {"from_attributes": True}
