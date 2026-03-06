from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProviderCreate(BaseModel):
    provider_name: str = Field(max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    api_key: str | None = Field(default=None, max_length=500)
    base_url: str | None = Field(default=None, max_length=500)
    available_models: list[str] | None = None
    is_active: bool = True

    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url 必须以 http:// 或 https:// 开头')
        return v


class ProviderUpdate(BaseModel):
    api_key: str | None = Field(default=None, max_length=500)
    base_url: str | None = Field(default=None, max_length=500)
    available_models: list[str] | None = None
    is_active: bool | None = None

    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url 必须以 http:// 或 https:// 开头')
        return v


class ProviderResponse(BaseModel):
    id: UUID
    provider_name: str
    api_key_set: bool
    base_url: str | None
    available_models: list[str] | None
    is_active: bool

    model_config = {"from_attributes": True}


class ModelOption(BaseModel):
    provider: str
    model: str
