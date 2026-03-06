import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class AgentVersion(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "agent_versions"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    endpoint: Mapped[str | None] = mapped_column(String(500))
    method: Mapped[str] = mapped_column(String(10), default="POST")
    auth_type: Mapped[str | None] = mapped_column(String(20))
    auth_token: Mapped[str | None] = mapped_column(String(500))
    request_template: Mapped[str | None] = mapped_column(Text)
    response_path: Mapped[str | None] = mapped_column(String(200))
    has_end_signal: Mapped[bool] = mapped_column(Boolean, default=False)
    end_signal_path: Mapped[str | None] = mapped_column(String(200))
    end_signal_value: Mapped[str | None] = mapped_column(String(100))
    connection_status: Mapped[str] = mapped_column(String(20), default="untested")

    project = relationship("Project", back_populates="agent_versions")
