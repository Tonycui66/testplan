import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class TestSuite(Base, UUIDMixin):
    __tablename__ = "test_suites"
    __table_args__ = {"schema": "test"}

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TestCase(Base, UUIDMixin):
    __tablename__ = "test_cases"
    __table_args__ = {"schema": "test"}

    suite_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    steps: Mapped[str] = mapped_column(Text, nullable=False)
    expected: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(10), default="medium", nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TestPlan(Base, UUIDMixin):
    __tablename__ = "test_plans"
    __table_args__ = {"schema": "test"}

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    iteration_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TestPlanCase(Base, UUIDMixin):
    __tablename__ = "test_plan_cases"
    __table_args__ = {"schema": "test"}

    plan_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class TestRun(Base, UUIDMixin):
    __tablename__ = "test_runs"
    __table_args__ = {"schema": "test"}

    plan_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    environment_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    started_by: Mapped[uuid.UUID] = mapped_column(nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class TestRunResult(Base, UUIDMixin):
    __tablename__ = "test_run_results"
    __table_args__ = {"schema": "test"}

    run_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    case_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(10), default="pending", nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    executed_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
