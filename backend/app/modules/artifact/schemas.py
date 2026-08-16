from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class RepositoryCreate(BaseModel):
    name: str = Field(max_length=200)
    type: str = "generic"
    description: Optional[str] = None


class ArtifactCreate(BaseModel):
    name: str = Field(max_length=255)
    version: str = Field(max_length=100)
    size_bytes: int
    storage_path: str = Field(max_length=500)
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = {}
