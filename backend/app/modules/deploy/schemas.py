from typing import Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class SshConfig(BaseModel):
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=22, ge=1, le=65535)
    username: str = Field(min_length=1, max_length=100)
    credential_ref: str = Field(min_length=1, max_length=200)


class K8sConfig(BaseModel):
    cluster_ref: str = Field(min_length=1, max_length=200)
    namespace: Optional[str] = Field(default=None, max_length=100)
    credential_ref: str = Field(min_length=1, max_length=200)


class EnvironmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: Literal["ssh", "k8s"] = "ssh"
    config: Optional[Union[SshConfig, K8sConfig]] = None
    is_protected: bool = False


class DeployTaskCreate(BaseModel):
    environment_id: UUID
    artifact_id: Optional[UUID] = None
    branch: Optional[str] = Field(default=None, max_length=255)
    commit_sha: Optional[str] = Field(default=None, max_length=40)
    strategy: Literal["rolling", "blue_green", "canary"] = "rolling"
