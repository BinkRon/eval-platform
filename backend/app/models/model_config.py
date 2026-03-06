import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class ModelConfig(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "model_configs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), unique=True
    )
    sparring_provider: Mapped[str | None] = mapped_column(String(50))
    sparring_model: Mapped[str | None] = mapped_column(String(100))
    sparring_temperature: Mapped[Decimal | None] = mapped_column(Numeric)
    sparring_max_tokens: Mapped[int | None] = mapped_column(Integer)
    sparring_system_prompt: Mapped[str | None] = mapped_column(Text)
    judge_provider: Mapped[str | None] = mapped_column(String(50))
    judge_model: Mapped[str | None] = mapped_column(String(100))
    judge_temperature: Mapped[Decimal | None] = mapped_column(Numeric)
    judge_max_tokens: Mapped[int | None] = mapped_column(Integer)
    judge_system_prompt: Mapped[str | None] = mapped_column(Text)

    project = relationship("Project", back_populates="model_config_")
