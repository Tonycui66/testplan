import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Project(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = {"schema": "project"}

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    key: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class ProjectMember(Base, UUIDMixin):
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
        {"schema": "project"},
    )

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Iteration(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "iterations"
    __table_args__ = {"schema": "project"}

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    goal: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="planning", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Requirement(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "requirements"
    __table_args__ = {"schema": "project"}

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    iteration_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    priority: Mapped[str] = mapped_column(String(10), default="medium", nullable=False)
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Task(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tasks"
    __table_args__ = {"schema": "project"}

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    iteration_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="todo", nullable=False)
    priority: Mapped[str] = mapped_column(String(10), default="medium", nullable=False)
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    estimated_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
    logged_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Bug(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "bugs"
    __table_args__ = {"schema": "project"}

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    iteration_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    steps_to_reproduce: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(10), default="medium", nullable=False)
    priority: Mapped[str] = mapped_column(String(10), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class RequirementTask(Base, UUIDMixin):
    __tablename__ = "requirement_tasks"
    __table_args__ = (
        UniqueConstraint("requirement_id", "task_id", name="uq_req_task"),
        {"schema": "project"},
    )

    requirement_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    task_id: Mapped[uuid.UUID] = mapped_column(nullable=False)


class TaskDependency(Base, UUIDMixin):
    __tablename__ = "task_dependencies"
    __table_args__ = (
        UniqueConstraint("task_id", "depends_on_id", name="uq_task_dep"),
        {"schema": "project"},
    )

    task_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    depends_on_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="blocks", nullable=False)


class Board(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "boards"
    __table_args__ = {"schema": "project"}

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(100), default="默认看板", nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="kanban", nullable=False)


class BoardColumn(Base, UUIDMixin):
    __tablename__ = "board_columns"
    __table_args__ = {"schema": "project"}

    board_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wip_limit: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BoardSwimlane(Base, UUIDMixin):
    __tablename__ = "board_swimlanes"
    __table_args__ = {"schema": "project"}

    board_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="none", nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BoardCard(Base, UUIDMixin):
    __tablename__ = "board_cards"
    __table_args__ = (
        UniqueConstraint("board_id", "item_type", "item_id", name="uq_card_item"),
        {"schema": "project"},
    )

    board_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    column_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    swimlane_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Label(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "labels"
    __table_args__ = {"schema": "project"}

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#6B7280", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class ItemLabel(Base, UUIDMixin):
    __tablename__ = "item_labels"
    __table_args__ = (
        UniqueConstraint("label_id", "item_type", "item_id", name="uq_label_item"),
        {"schema": "project"},
    )

    label_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
