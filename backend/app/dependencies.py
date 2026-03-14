"""FastAPI dependencies for authentication."""

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import AuthenticationError
from app.models.user import User
from app.services.auth_service import get_user_by_id, verify_token


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Extract and validate JWT from Authorization header, return the current user."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationError("未提供认证令牌")

    token = auth_header[7:]  # Strip "Bearer "
    user_id = verify_token(token)

    user = await get_user_by_id(db, user_id)
    if not user:
        raise AuthenticationError("用户不存在")
    if not user.is_active:
        raise AuthenticationError("账号已被禁用")

    return user
