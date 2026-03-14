"""Authentication service — register, login, JWT token management."""

from datetime import datetime, timezone, timedelta
from uuid import UUID

import bcrypt as _bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import AuthenticationError, ConflictError, ValidationError
from app.models.user import User
from app.schemas.auth import TokenResponse, UserResponse


async def register(db: AsyncSession, username: str, password: str, email: str | None = None) -> UserResponse:
    """Register a new user."""
    existing = await db.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none():
        raise ConflictError(f"用户名 '{username}' 已存在")

    if email:
        existing_email = await db.execute(select(User).where(User.email == email))
        if existing_email.scalar_one_or_none():
            raise ConflictError(f"邮箱 '{email}' 已被注册")

    user = User(
        username=username,
        password_hash=_hash_password(password),
        email=email,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _to_response(user)


async def login(db: AsyncSession, username: str, password: str) -> TokenResponse:
    """Authenticate user and return JWT token."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not _verify_password(password, user.password_hash):
        raise AuthenticationError("用户名或密码错误")
    if not user.is_active:
        raise AuthenticationError("账号已被禁用")

    token = _create_token(user.id)
    return TokenResponse(access_token=token)


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    """Get user by ID."""
    return await db.get(User, user_id)


def verify_token(token: str) -> UUID:
    """Verify JWT token and return user_id. Raises AuthenticationError on failure."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return UUID(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("登录已过期，请重新登录")
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise AuthenticationError("无效的认证令牌")


def _hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def _verify_password(password: str, password_hash: str) -> bool:
    return _bcrypt.checkpw(password.encode(), password_hash.encode())


def _create_token(user_id: UUID) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        role=user.role,
    )
