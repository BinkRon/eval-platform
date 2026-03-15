from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.provider import ModelOption, ProviderCreate, ProviderResponse, ProviderTestResult, ProviderUpdate
from app.services import provider_service

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("", response_model=list[ProviderResponse])
async def list_providers(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    """获取所有模型供应商列表。"""
    return await provider_service.list_providers(db)


@router.get("/models", response_model=list[ModelOption])
async def list_available_models(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    """获取所有启用供应商的可用模型列表（供下拉选择）。"""
    return await provider_service.list_available_models(db)


@router.post("", response_model=ProviderResponse, status_code=201)
async def create_provider(data: ProviderCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    """创建新的模型供应商。"""
    return await provider_service.create_provider(db, data)


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(provider_id: UUID, data: ProviderUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    """更新供应商配置。"""
    return await provider_service.update_provider(db, provider_id, data)


@router.post("/{provider_id}/test", response_model=ProviderTestResult)
async def test_provider_connection(provider_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    """测试供应商 API Key 的连通性（使用第一个可用模型发送测试请求）。"""
    return await provider_service.test_connection(db, provider_id)


@router.delete("/{provider_id}", status_code=204)
async def delete_provider(provider_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    """删除模型供应商。"""
    await provider_service.delete_provider(db, provider_id)
