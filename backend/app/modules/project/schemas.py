from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    key: str = Field(min_length=1, max_length=10)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    key: str
    description: Optional[str] = None
    is_archived: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberCreate(BaseModel):
    user_id: UUID
    role: str = "member"


class MemberUpdate(BaseModel):
    role: str


class MemberResponse(BaseModel):
    user_id: UUID
    role: str


class IterationCreate(BaseModel):
    name: str
    goal: Optional[str] = None
    start_date: date
    end_date: date


class IterationUpdate(BaseModel):
    name: Optional[str] = None
    goal: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class RequirementCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    iteration_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "todo"
    priority: str = "medium"
    assignee_id: Optional[UUID] = None
    requirement_id: Optional[UUID] = None
    iteration_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None


class BugCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = "medium"
    priority: str = "medium"
    assignee_id: Optional[UUID] = None
    iteration_id: Optional[UUID] = None


class BoardColumnCreate(BaseModel):
    name: str
    order: int = 0


class BoardColumnUpdate(BaseModel):
    name: Optional[str] = None
    order: Optional[int] = None

class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[UUID] = None
    iteration_id: Optional[UUID] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[UUID] = None
    iteration_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None


class BugUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    steps_to_reproduce: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee_id: Optional[UUID] = None
    iteration_id: Optional[UUID] = None
