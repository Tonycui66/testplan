import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class Environment(Base, UUIDMixin):
    __tablename__ = "environments"
    __table_args__ = {"schema": "deploy"}

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="ssh", nullable=False)
    config: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DeployTask(Base, UUIDMixin):
    __tablename__ = "deploy_tasks"
    __table_args__ = {"schema": "deploy"}

    environment_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    branch: Mapped[Optional[str]] = mapped_column(String(255))
    commit_sha: Mapped[Optional[str]] = mapped_column(String(40))
    strategy: Mapped[str] = mapped_column(String(20), default="rolling", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    trigger_user_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class DeployRecord(Base, UUIDMixin):
    __tablename__ = "deploy_records"
    __table_args__ = {"schema": "deploy"}

    task_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    environment_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    log: Mapped[Optional[str]] = mapped_column(Text)
    deployed_by: Mapped[uuid.UUID] = mapped_column(nullable=False)
    deployed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SshCredential(Base, UUIDMixin):
    __tablename__ = "ssh_credentials"
    __table_args__ = {"schema": "deploy"}

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=22, nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    private_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)


class K8sCluster(Base, UUIDMixin):
    __tablename__ = "k8s_clusters"
    __table_args__ = {"schema": "deploy"}

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    kubeconfig_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
