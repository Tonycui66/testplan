from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RepositoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: Literal["generic", "docker", "maven", "npm"] = "generic"
    description: Optional[str] = Field(default=None, max_length=2000)


class ArtifactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    version: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(ge=0)
    storage_path: Optional[str] = Field(default=None, max_length=500)
    checksum: Optional[str] = Field(default=None, pattern=r"^[a-fA-F0-9]{1,64}$")
    metadata: Dict[str, Any] = {}
