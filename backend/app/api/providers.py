from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.provider import ModelOption, ProviderCreate, ProviderResponse, ProviderUpdate
from app.services import provider_service

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("", response_model=list[ProviderResponse])
async def list_providers(db: AsyncSession = Depends(get_db)):
    return await provider_service.list_providers(db)


@router.get("/models", response_model=list[ModelOption])
async def list_available_models(db: AsyncSession = Depends(get_db)):
    return await provider_service.list_available_models(db)


@router.post("", response_model=ProviderResponse, status_code=201)
async def create_provider(data: ProviderCreate, db: AsyncSession = Depends(get_db)):
    return await provider_service.create_provider(db, data)


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(provider_id: UUID, data: ProviderUpdate, db: AsyncSession = Depends(get_db)):
    return await provider_service.update_provider(db, provider_id, data)


@router.delete("/{provider_id}", status_code=204)
async def delete_provider(provider_id: UUID, db: AsyncSession = Depends(get_db)):
    await provider_service.delete_provider(db, provider_id)
