from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EnvironmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: Literal["ssh", "k8s"] = "ssh"
    config: Dict[str, Any] = {}
    is_protected: bool = False


class DeployTaskCreate(BaseModel):
    environment_id: UUID
    artifact_id: Optional[UUID] = None
    branch: Optional[str] = Field(default=None, max_length=255)
    commit_sha: Optional[str] = Field(default=None, max_length=40)
    strategy: Literal["rolling", "blue_green", "canary"] = "rolling"
