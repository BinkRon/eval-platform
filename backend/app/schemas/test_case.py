"""测试用例相关的请求/响应模型。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TestCaseCreate(BaseModel):
    """创建测试用例。"""

    name: str = Field(max_length=100, description="用例名称", examples=["退款咨询场景"])
    sparring_prompt: str = Field(min_length=1, description="对练机器人角色 Prompt，描述模拟用户的行为")
    first_message: str | None = Field(default=None, description="首条消息（由对练机器人发出，开启对话）")
    max_rounds: int = Field(default=50, ge=3, le=100, description="最大对话轮次，3-100")
    sort_order: int = Field(default=0, description="排序序号")


class TestCaseUpdate(BaseModel):
    """更新测试用例（部分更新）。"""

    name: str | None = Field(default=None, max_length=100, description="用例名称")
    sparring_prompt: str | None = Field(default=None, min_length=1, description="对练机器人角色 Prompt")
    first_message: str | None = Field(default=None, description="首条消息")
    max_rounds: int | None = Field(default=None, ge=3, le=100, description="最大对话轮次")
    sort_order: int | None = Field(default=None, description="排序序号")


class TestCaseResponse(BaseModel):
    """测试用例详情。"""

    id: UUID = Field(description="用例 ID")
    project_id: UUID = Field(description="所属项目 ID")
    name: str = Field(description="用例名称")
    sparring_prompt: str = Field(description="对练机器人角色 Prompt")
    first_message: str | None = Field(description="首条消息")
    max_rounds: int = Field(description="最大对话轮次")
    sort_order: int = Field(description="排序序号")
    last_result: str | None = Field(default=None, description="最近一次测试结果：passed / failed / error")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="最后更新时间")

    model_config = {"from_attributes": True}
