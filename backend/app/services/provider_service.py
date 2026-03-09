from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models.provider_config import ProviderConfig
from app.schemas.provider import ModelOption, ProviderCreate, ProviderResponse, ProviderUpdate


def _to_response(p: ProviderConfig) -> ProviderResponse:
    return ProviderResponse(
        id=p.id,
        provider_name=p.provider_name,
        api_key_set=bool(p.api_key),
        base_url=p.base_url,
        available_models=p.available_models,
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
        if p.available_models:
            for m in p.available_models:
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
        api_key=data.api_key,
        base_url=data.base_url,
        available_models=data.available_models,
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
        setattr(provider, key, value)
    await db.commit()
    await db.refresh(provider)
    return _to_response(provider)


async def delete_provider(db: AsyncSession, provider_id: UUID) -> None:
    provider = await db.get(ProviderConfig, provider_id)
    if not provider:
        raise NotFoundError("供应商不存在")
    await db.delete(provider)
    await db.commit()
