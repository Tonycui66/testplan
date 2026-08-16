from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class SuiteCreate(BaseModel):
    name: str = Field(max_length=200)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None


class CaseCreate(BaseModel):
    suite_id: UUID
    title: str = Field(max_length=500)
    steps: str
    expected: str
    priority: str = "medium"
    type: str = "manual"


class PlanCreate(BaseModel):
    name: str = Field(max_length=200)
    iteration_id: Optional[UUID] = None
    case_ids: List[UUID] = []
