from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MessageData(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1)


class AppendMessageRequest(BaseModel):
    message: MessageData


class BuilderConversationResponse(BaseModel):
    id: UUID
    project_id: UUID
    messages: list[MessageData]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
