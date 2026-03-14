"""Tests for the auth service — register, login, JWT verification."""

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import bcrypt as _bcrypt
import jwt
import pytest

from app.services.auth_service import login, register, verify_token


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_user():
    return SimpleNamespace(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash=_bcrypt.hashpw(b"password123", _bcrypt.gensalt()).decode(),
        is_active=True,
        role="user",
    )


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        user = SimpleNamespace(
            id=uuid.uuid4(), username="newuser", email=None,
            password_hash="hashed", is_active=True, role="user",
        )
        mock_db.refresh = AsyncMock(side_effect=lambda u: setattr(u, 'id', user.id) or setattr(u, 'is_active', True) or setattr(u, 'role', 'user'))

        result = await register(mock_db, "newuser", "password123")
        assert result.username == "newuser"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = SimpleNamespace(username="existing")
        mock_db.execute = AsyncMock(return_value=mock_result)

        from app.exceptions import ConflictError
        with pytest.raises(ConflictError, match="已存在"):
            await register(mock_db, "existing", "password123")


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, mock_db, mock_user):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await login(mock_db, "testuser", "password123")
        assert result.access_token
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, mock_db, mock_user):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        from app.exceptions import AuthenticationError
        with pytest.raises(AuthenticationError, match="用户名或密码错误"):
            await login(mock_db, "testuser", "wrongpassword")

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        from app.exceptions import AuthenticationError
        with pytest.raises(AuthenticationError, match="用户名或密码错误"):
            await login(mock_db, "nobody", "password")

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, mock_db, mock_user):
        mock_user.is_active = False
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        from app.exceptions import AuthenticationError
        with pytest.raises(AuthenticationError, match="账号已被禁用"):
            await login(mock_db, "testuser", "password123")


class TestVerifyToken:
    def test_valid_token(self):
        from app.config import settings
        user_id = uuid.uuid4()
        token = jwt.encode(
            {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            settings.jwt_secret, algorithm="HS256"
        )
        assert verify_token(token) == user_id

    def test_expired_token(self):
        from app.config import settings
        token = jwt.encode(
            {"sub": str(uuid.uuid4()), "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            settings.jwt_secret, algorithm="HS256"
        )
        from app.exceptions import AuthenticationError
        with pytest.raises(AuthenticationError, match="过期"):
            verify_token(token)

    def test_tampered_token(self):
        token = jwt.encode(
            {"sub": str(uuid.uuid4()), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "wrong-secret", algorithm="HS256"
        )
        from app.exceptions import AuthenticationError
        with pytest.raises(AuthenticationError, match="无效"):
            verify_token(token)

    def test_malformed_token(self):
        from app.exceptions import AuthenticationError
        with pytest.raises(AuthenticationError, match="无效"):
            verify_token("not-a-jwt-token")
