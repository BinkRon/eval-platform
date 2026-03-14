"""FastAPI dependencies for authentication and authorization."""

from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import AuthenticationError, NotFoundError
from app.models.project import Project
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
        # Double-check: login already checks is_active, but token may outlive account deactivation
        raise AuthenticationError("账号已被禁用")

    return user


async def verify_project_access(
    project_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Project:
    """Verify the current user owns the project. Used by sub-resource routes.

    Returns 404 (not 403) to avoid disclosing whether the project exists to unauthorized users.
    """
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise NotFoundError("项目不存在")
    return project
