import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class BatchTest(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "batch_tests"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    agent_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agent_versions.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    concurrency: Mapped[int] = mapped_column(Integer, default=3)
    total_cases: Mapped[int] = mapped_column(Integer, default=0)
    passed_cases: Mapped[int] = mapped_column(Integer, default=0)
    completed_cases: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    project = relationship("Project", back_populates="batch_tests")
    agent_version = relationship("AgentVersion")
    test_results = relationship("TestResult", back_populates="batch_test", cascade="all, delete-orphan")


class TestResult(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "test_results"

    batch_test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batch_tests.id", ondelete="CASCADE")
    )
    test_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_cases.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
    conversation: Mapped[list | None] = mapped_column(JSONB)
    termination_reason: Mapped[str | None] = mapped_column(String(20))
    actual_rounds: Mapped[int | None] = mapped_column(Integer)
    checklist_results: Mapped[list | None] = mapped_column(JSONB)
    eval_scores: Mapped[list | None] = mapped_column(JSONB)
    judge_summary: Mapped[str | None] = mapped_column(Text)
    passed: Mapped[bool | None] = mapped_column(Boolean)
    error_message: Mapped[str | None] = mapped_column(Text)

    batch_test = relationship("BatchTest", back_populates="test_results")
