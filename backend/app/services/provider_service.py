from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.llm.factory import create_llm_adapter
from app.models.provider_config import ProviderConfig
from app.utils.crypto import decrypt, encrypt
from app.utils.error_sanitizer import sanitize_error
from app.schemas.provider import ModelOption, ProviderCreate, ProviderResponse, ProviderTestResult, ProviderUpdate


def _clean_available_models(models: list[str] | None) -> list[str] | None:
    if not models:
        return None
    cleaned = [m.strip() for m in models if m and m.strip()]
    return cleaned or None


def _to_response(p: ProviderConfig) -> ProviderResponse:
    return ProviderResponse(
        id=p.id,
        provider_name=p.provider_name,
        api_key_set=bool(p.api_key),
        base_url=p.base_url,
        available_models=_clean_available_models(p.available_models),
        is_active=p.is_active,
    )


async def list_providers(db: AsyncSession) -> list[ProviderResponse]:
    result = await db.execute(select(ProviderConfig).order_by(ProviderConfig.created_at))
    return [_to_response(p) for p in result.scalars().all()]


async def list_available_models(db: AsyncSession) -> list[ModelOption]:
    result = await db.execute(
        select(ProviderConfig).where(ProviderConfig.is_active.is_(True))
    )
    models = []
    for p in result.scalars().all():
        cleaned_models = _clean_available_models(p.available_models)
        if cleaned_models:
            for m in cleaned_models:
                models.append(ModelOption(provider=p.provider_name, model=m))
    return models


async def create_provider(db: AsyncSession, data: ProviderCreate) -> ProviderResponse:
    existing = await db.execute(
        select(ProviderConfig).where(ProviderConfig.provider_name == data.provider_name)
    )
    if existing.scalar_one_or_none():
        raise ConflictError(f"供应商 '{data.provider_name}' 已存在")

    provider = ProviderConfig(
        provider_name=data.provider_name,
        api_key=encrypt(data.api_key) if data.api_key else data.api_key,
        base_url=data.base_url,
        available_models=_clean_available_models(data.available_models),
        is_active=data.is_active,
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)
    return _to_response(provider)


async def update_provider(db: AsyncSession, provider_id: UUID, data: ProviderUpdate) -> ProviderResponse:
    provider = await db.get(ProviderConfig, provider_id)
    if not provider:
        raise NotFoundError("供应商不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        if key == "available_models":
            value = _clean_available_models(value)
        elif key == "api_key" and value:
            value = encrypt(value)
        setattr(provider, key, value)
    await db.commit()
    await db.refresh(provider)
    return _to_response(provider)


async def test_connection(db: AsyncSession, provider_id: UUID) -> ProviderTestResult:
    provider = await db.get(ProviderConfig, provider_id)
    if not provider:
        raise NotFoundError("供应商不存在")

    if not provider.api_key:
        raise ValidationError("未配置 API Key")

    models = _clean_available_models(provider.available_models)
    if not models:
        raise ValidationError("未配置可用模型")

    try:
        api_key = decrypt(provider.api_key)
        adapter = create_llm_adapter(
            provider_name=provider.provider_name,
            api_key=api_key,
            model=models[0],
            base_url=provider.base_url,
        )
        await adapter.chat(
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=16,
        )
        return ProviderTestResult(status="success")
    except Exception as e:
        return ProviderTestResult(status="failed", error=sanitize_error(str(e)))


async def delete_provider(db: AsyncSession, provider_id: UUID) -> None:
    provider = await db.get(ProviderConfig, provider_id)
    if not provider:
        raise NotFoundError("供应商不存在")
    await db.delete(provider)
    await db.commit()
