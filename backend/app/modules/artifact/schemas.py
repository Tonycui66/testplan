from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RepositoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: Literal["generic", "docker", "maven", "npm"] = "generic"
    description: Optional[str] = Field(default=None, max_length=2000)


class ArtifactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    version: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("name", "version")
    @classmethod
    def reject_dot_segments(cls, value: str) -> str:
        if value in {".", ".."}:
            raise ValueError("name/version cannot be dot segments")
        return value
