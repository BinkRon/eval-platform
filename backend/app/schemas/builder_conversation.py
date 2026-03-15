"""构建助手对话相关的请求/响应模型。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MessageData(BaseModel):
    """单条对话消息。"""

    role: str = Field(pattern="^(user|assistant)$", description="消息角色：user 或 assistant")
    content: str = Field(min_length=1, description="消息内容")


class AppendMessageRequest(BaseModel):
    """追加消息到构建对话。"""

    message: MessageData = Field(description="要追加的消息")


class BuilderConversationResponse(BaseModel):
    """构建助手对话详情。"""

    id: UUID = Field(description="对话 ID")
    project_id: UUID = Field(description="所属项目 ID")
    messages: list[MessageData] = Field(description="对话消息列表")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="最后更新时间")

    model_config = {"from_attributes": True}
