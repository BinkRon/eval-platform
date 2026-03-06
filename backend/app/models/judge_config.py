import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class JudgeConfig(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "judge_configs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), unique=True
    )
    pass_threshold: Mapped[Decimal] = mapped_column(Numeric(3, 1), default=Decimal("2.0"))

    project = relationship("Project", back_populates="judge_config", lazy="raise")
    checklist_items = relationship("ChecklistItem", back_populates="judge_config", cascade="all, delete-orphan", lazy="raise")
    eval_dimensions = relationship("EvalDimension", back_populates="judge_config", cascade="all, delete-orphan", lazy="raise")


class ChecklistItem(UUIDPrimaryKey, Base):
    __tablename__ = "checklist_items"

    judge_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("judge_configs.id", ondelete="CASCADE")
    )
    content: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(20), default="must")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    judge_config = relationship("JudgeConfig", back_populates="checklist_items", lazy="raise")


class EvalDimension(UUIDPrimaryKey, Base):
    __tablename__ = "eval_dimensions"

    judge_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("judge_configs.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    level_3_desc: Mapped[str | None] = mapped_column(Text)
    level_2_desc: Mapped[str | None] = mapped_column(Text)
    level_1_desc: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    judge_config = relationship("JudgeConfig", back_populates="eval_dimensions", lazy="raise")
