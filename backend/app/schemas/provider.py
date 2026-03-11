from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _strip_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _strip_model_list(values: list[str] | None) -> list[str] | None:
    if values is None:
        return None
    cleaned = [value.strip() for value in values if value and value.strip()]
    return cleaned or None


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

    @field_validator('api_key', mode='before')
    @classmethod
    def strip_api_key(cls, v: str | None) -> str | None:
        return _strip_optional_string(v)

    @field_validator('available_models', mode='before')
    @classmethod
    def strip_available_models(cls, v: list[str] | None) -> list[str] | None:
        return _strip_model_list(v)


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

    @field_validator('api_key', mode='before')
    @classmethod
    def strip_api_key(cls, v: str | None) -> str | None:
        return _strip_optional_string(v)

    @field_validator('available_models', mode='before')
    @classmethod
    def strip_available_models(cls, v: list[str] | None) -> list[str] | None:
        return _strip_model_list(v)


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
