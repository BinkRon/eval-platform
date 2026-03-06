from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class Project(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)

    agent_versions = relationship("AgentVersion", back_populates="project", cascade="all, delete-orphan")
    test_cases = relationship("TestCase", back_populates="project", cascade="all, delete-orphan")
    judge_config = relationship("JudgeConfig", back_populates="project", uselist=False, cascade="all, delete-orphan")
    model_config_ = relationship("ModelConfig", back_populates="project", uselist=False, cascade="all, delete-orphan")
    batch_tests = relationship("BatchTest", back_populates="project", cascade="all, delete-orphan")
