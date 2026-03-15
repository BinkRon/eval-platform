"""模型供应商相关的请求/响应模型。"""

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
    """创建模型供应商。"""

    provider_name: str = Field(max_length=50, pattern=r'^[a-zA-Z0-9_-]+$', description="供应商标识（唯一），仅允许字母、数字、下划线、连字符", examples=["openai"])
    api_key: str | None = Field(default=None, max_length=500, description="API Key（保存后不回显）")
    base_url: str | None = Field(default=None, max_length=500, description="自定义 API 地址", examples=["https://api.openai.com/v1"])
    available_models: list[str] | None = Field(default=None, description="可用模型列表", examples=[["gpt-4o", "gpt-4o-mini"]])
    is_active: bool = Field(default=True, description="是否启用")

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
    """更新供应商信息（部分更新）。"""

    api_key: str | None = Field(default=None, max_length=500, description="API Key（空值表示不更新）")
    base_url: str | None = Field(default=None, max_length=500, description="自定义 API 地址")
    available_models: list[str] | None = Field(default=None, description="可用模型列表")
    is_active: bool | None = Field(default=None, description="是否启用")

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
    """供应商详情。"""

    id: UUID = Field(description="供应商 ID")
    provider_name: str = Field(description="供应商标识")
    api_key_set: bool = Field(description="是否已设置 API Key（不返回实际值）")
    base_url: str | None = Field(description="自定义 API 地址")
    available_models: list[str] | None = Field(description="可用模型列表")
    is_active: bool = Field(description="是否启用")

    model_config = {"from_attributes": True}


class ProviderTestResult(BaseModel):
    """供应商连通性测试结果。"""

    status: str = Field(description="测试状态：success 或 failed")
    error: str | None = Field(default=None, description="错误信息（失败时）")


class ModelOption(BaseModel):
    """可选模型（供应商 + 模型名组合）。"""

    provider: str = Field(description="供应商标识")
    model: str = Field(description="模型名称")
