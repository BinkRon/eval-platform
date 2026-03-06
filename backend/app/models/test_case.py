import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class TestCase(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "test_cases"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    first_message: Mapped[str] = mapped_column(Text)
    persona_background: Mapped[str | None] = mapped_column(Text)
    persona_behavior: Mapped[str | None] = mapped_column(Text)
    max_rounds: Mapped[int] = mapped_column(Integer, default=20)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    project = relationship("Project", back_populates="test_cases", lazy="raise")
