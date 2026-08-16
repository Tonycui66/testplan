from __future__ import annotations
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SuiteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    parent_id: Optional[UUID] = None


class CaseCreate(BaseModel):
    suite_id: UUID
    title: str = Field(min_length=1, max_length=500)
    steps: str = Field(min_length=1)
    expected: str = Field(min_length=1)
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    type: Literal["manual", "api", "e2e"] = "manual"


class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    iteration_id: Optional[UUID] = None
    case_ids: List[UUID] = []
