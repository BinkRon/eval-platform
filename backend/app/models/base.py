import uuid
from datetime import datetime

from sqlalchemy import DateTime, event, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class UUIDPrimaryKey:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


@event.listens_for(Session, "before_flush")
def _set_updated_at(session: Session, flush_context, instances):
    for obj in session.dirty:
        if hasattr(obj, "updated_at"):
            obj.updated_at = func.now()
