from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class EnvironmentCreate(BaseModel):
    name: str = Field(max_length=100)
    type: str = "ssh"
    config: Dict[str, Any] = {}
    is_protected: bool = False


class DeployTaskCreate(BaseModel):
    environment_id: UUID
    artifact_id: Optional[UUID] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    strategy: str = "rolling"
