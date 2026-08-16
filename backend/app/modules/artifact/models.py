import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import BigInteger, DateTime, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class ArtifactRepository(Base, UUIDMixin):
    __tablename__ = "repositories"
    __table_args__ = {"schema": "artifact"}

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="generic", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Artifact(Base, UUIDMixin):
    __tablename__ = "artifacts"
    __table_args__ = {"schema": "artifact"}

    repository_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(64))
    artifact_metadata: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)


class DockerImage(Base, UUIDMixin):
    __tablename__ = "docker_images"
    __table_args__ = {"schema": "artifact"}

    repository_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    image_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tag: Mapped[str] = mapped_column(String(100), nullable=False)
    digest: Mapped[Optional[str]] = mapped_column(String(71))
    size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger)
    pushed_by: Mapped[uuid.UUID] = mapped_column(nullable=False)


class ArtifactVersion(Base, UUIDMixin):
    __tablename__ = "artifact_versions"
    __table_args__ = {"schema": "artifact"}

    repository_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    release_notes: Mapped[Optional[str]] = mapped_column(Text)
    pipeline_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
