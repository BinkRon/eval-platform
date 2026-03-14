"""认证相关的请求/响应模型。"""

from uuid import UUID

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """用户注册请求。"""

    username: str = Field(min_length=2, max_length=50, description="用户名，2-50 字符，全局唯一")
    password: str = Field(min_length=6, max_length=100, description="密码，至少 6 位")
    email: str | None = Field(default=None, max_length=200, description="邮箱地址（可选）")


class LoginRequest(BaseModel):
    """用户登录请求。"""

    username: str = Field(description="用户名")
    password: str = Field(description="密码")


class TokenResponse(BaseModel):
    """登录成功后返回的 JWT Token。"""

    access_token: str = Field(description="JWT 访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型，固定为 bearer")


class UserResponse(BaseModel):
    """用户信息响应。"""

    id: UUID = Field(description="用户 ID")
    username: str = Field(description="用户名")
    email: str | None = Field(description="邮箱地址")
    is_active: bool = Field(description="账号是否启用")
    role: str = Field(description="用户角色。admin: 管理员；user: 普通用户")
