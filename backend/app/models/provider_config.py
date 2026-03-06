from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class ProviderConfig(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "provider_configs"

    provider_name: Mapped[str] = mapped_column(String(50), unique=True)
    api_key: Mapped[str | None] = mapped_column(String(500))
    base_url: Mapped[str | None] = mapped_column(String(500))
    available_models: Mapped[list | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
