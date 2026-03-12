import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class BuilderConversation(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "builder_conversations"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), unique=True
    )
    messages: Mapped[list] = mapped_column(JSONB, default=list)

    project = relationship("Project", back_populates="builder_conversation", lazy="raise")
