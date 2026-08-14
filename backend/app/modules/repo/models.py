import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class RepoConnection(Base, UUIDMixin):
    __tablename__ = "repo_connections"
    __table_args__ = {"schema": "repo"}

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    repo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(200), nullable=False)
    oauth_token_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WebhookEvent(Base, UUIDMixin):
    __tablename__ = "webhook_events"
    __table_args__ = {"schema": "repo"}

    connection_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    dedupe_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Branch(Base, UUIDMixin):
    __tablename__ = "branches"
    __table_args__ = {"schema": "repo"}

    connection_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_commit_sha: Mapped[Optional[str]] = mapped_column(String(40))
    last_commit_message: Mapped[Optional[str]] = mapped_column(Text)
    last_commit_author: Mapped[Optional[str]] = mapped_column(String(255))
    last_commit_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Commit(Base, UUIDMixin):
    __tablename__ = "commits"
    __table_args__ = {"schema": "repo"}

    connection_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    branch: Mapped[str] = mapped_column(String(255), nullable=False)
    sha: Mapped[str] = mapped_column(String(40), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    author_email: Mapped[str] = mapped_column(String(255), nullable=False)
    committed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
