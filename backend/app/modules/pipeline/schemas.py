from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StageInput(BaseModel):
    name: str
    order: int = 0
    condition: Literal["always", "on_success", "on_failure"] = "always"
    jobs: List["JobInput"]


class JobInput(BaseModel):
    name: str
    image: str
    script: str
    timeout_seconds: int = Field(default=3600, ge=1)
    order: int = 0
    variables: Dict[str, Any] = {}


StageInput.model_rebuild()


class PipelineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    stages: List[StageInput] = []


class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    stages: Optional[List[StageInput]] = None


class PipelineResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str] = None
    is_enabled: bool = True
    run_counter: int = 0

    model_config = {"from_attributes": True}


class RunCreate(BaseModel):
    trigger_type: Literal["manual", "push", "webhook", "schedule"] = "manual"
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    variables: Dict[str, Any] = {}
