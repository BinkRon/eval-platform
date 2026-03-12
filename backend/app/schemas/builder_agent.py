from pydantic import BaseModel, Field


class BuilderChatRequest(BaseModel):
    message: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)


class BuilderChatResponse(BaseModel):
    response: str
