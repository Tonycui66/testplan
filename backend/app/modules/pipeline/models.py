import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Pipeline(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "pipelines"
    __table_args__ = {"schema": "pipeline"}

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    run_counter: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class PipelineStage(Base, UUIDMixin):
    __tablename__ = "pipeline_stages"
    __table_args__ = {"schema": "pipeline"}

    pipeline_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    condition: Mapped[str] = mapped_column(String(20), default="always", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PipelineJob(Base, UUIDMixin):
    __tablename__ = "pipeline_jobs"
    __table_args__ = {"schema": "pipeline"}

    stage_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    image: Mapped[str] = mapped_column(String(500), nullable=False)
    script: Mapped[str] = mapped_column(Text, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    variables: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PipelineTrigger(Base, UUIDMixin):
    __tablename__ = "pipeline_triggers"
    __table_args__ = {"schema": "pipeline"}

    pipeline_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    config: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PipelineRun(Base, UUIDMixin):
    __tablename__ = "pipeline_runs"
    __table_args__ = {"schema": "pipeline"}

    pipeline_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(20), nullable=False)
    trigger_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    branch: Mapped[Optional[str]] = mapped_column(String(255))
    commit_sha: Mapped[Optional[str]] = mapped_column(String(40))
    variables: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class StageRun(Base, UUIDMixin):
    __tablename__ = "stage_runs"
    __table_args__ = {"schema": "pipeline"}

    run_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    stage_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class JobRun(Base, UUIDMixin):
    __tablename__ = "job_runs"
    __table_args__ = {"schema": "pipeline"}

    stage_run_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class JobLog(Base, UUIDMixin):
    __tablename__ = "job_logs"
    __table_args__ = {"schema": "pipeline"}

    job_run_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    stream: Mapped[str] = mapped_column(String(6), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
