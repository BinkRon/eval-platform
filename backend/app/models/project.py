from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class Project(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)

    agent_versions = relationship("AgentVersion", back_populates="project", cascade="all, delete-orphan", lazy="raise")
    test_cases = relationship("TestCase", back_populates="project", cascade="all, delete-orphan", lazy="raise")
    judge_config = relationship("JudgeConfig", back_populates="project", uselist=False, cascade="all, delete-orphan", lazy="raise")
    model_config_ = relationship("ModelConfig", back_populates="project", uselist=False, cascade="all, delete-orphan", lazy="raise")
    batch_tests = relationship("BatchTest", back_populates="project", cascade="all, delete-orphan", lazy="raise")
    project_files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan", lazy="raise")
    builder_conversation = relationship("BuilderConversation", back_populates="project", uselist=False, cascade="all, delete-orphan", lazy="raise")
