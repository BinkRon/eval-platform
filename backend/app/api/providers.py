from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.provider_config import ProviderConfig
from app.schemas.provider import ModelOption, ProviderCreate, ProviderResponse, ProviderUpdate

router = APIRouter(prefix="/api/providers", tags=["providers"])


def _to_response(p: ProviderConfig) -> ProviderResponse:
    return ProviderResponse(
        id=p.id,
        provider_name=p.provider_name,
        api_key_set=bool(p.api_key),
        base_url=p.base_url,
        available_models=p.available_models,
        is_active=p.is_active,
    )


@router.get("/", response_model=list[ProviderResponse])
async def list_providers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProviderConfig).order_by(ProviderConfig.created_at))
    return [_to_response(p) for p in result.scalars().all()]


@router.get("/models", response_model=list[ModelOption])
async def list_available_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProviderConfig).where(ProviderConfig.is_active.is_(True))
    )
    models = []
    for p in result.scalars().all():
        if p.available_models:
            for m in p.available_models:
                models.append(ModelOption(provider=p.provider_name, model=m))
    return models


@router.post("/", response_model=ProviderResponse, status_code=201)
async def create_provider(data: ProviderCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(ProviderConfig).where(ProviderConfig.provider_name == data.provider_name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, detail=f"Provider '{data.provider_name}' already exists")

    provider = ProviderConfig(
        provider_name=data.provider_name,
        api_key=data.api_key,
        base_url=data.base_url,
        available_models=data.available_models,
        is_active=data.is_active,
    )
    db.add(provider)
    await db.commit()
    return _to_response(provider)


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(provider_id: UUID, data: ProviderUpdate, db: AsyncSession = Depends(get_db)):
    provider = await db.get(ProviderConfig, provider_id)
    if not provider:
        raise HTTPException(404, detail="Provider not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(provider, key, value)

    await db.commit()
    return _to_response(provider)


@router.delete("/{provider_id}", status_code=204)
async def delete_provider(provider_id: UUID, db: AsyncSession = Depends(get_db)):
    provider = await db.get(ProviderConfig, provider_id)
    if not provider:
        raise HTTPException(404, detail="Provider not found")

    await db.delete(provider)
    await db.commit()
