from uuid import UUID

from pydantic import BaseModel


class ProviderCreate(BaseModel):
    provider_name: str
    api_key: str | None = None
    base_url: str | None = None
    available_models: list[str] | None = None
    is_active: bool = True


class ProviderUpdate(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    available_models: list[str] | None = None
    is_active: bool | None = None


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
