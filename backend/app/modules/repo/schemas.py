from datetime import datetime
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RepoConnectionCreate(BaseModel):
    provider: Literal["github", "gitlab"] = "github"
    repo_url: str = Field(max_length=500)
    repo_name: str = Field(max_length=200)
    oauth_token_id: Optional[UUID] = None


class RepoConnectionResponse(BaseModel):
    id: UUID
    project_id: UUID
    provider: str
    repo_url: str
    repo_name: str
    oauth_token_id: Optional[UUID] = None
    is_active: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookEventCreate(BaseModel):
    event_type: str = Field(max_length=50)
    payload: Dict[str, Any]
