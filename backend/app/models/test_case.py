import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class TestCase(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "test_cases"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    sparring_prompt: Mapped[str] = mapped_column(Text)
    first_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_rounds: Mapped[int] = mapped_column(Integer, default=50)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    project = relationship("Project", back_populates="test_cases", lazy="raise")
