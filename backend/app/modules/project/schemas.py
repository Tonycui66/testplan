from datetime import date, datetime
from typing import Literal, Optional
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
    role: Literal["owner", "member", "viewer"] = "member"


class MemberUpdate(BaseModel):
    role: Literal["owner", "member", "viewer"]


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
    status: Optional[Literal["planning", "active", "closed"]] = None


class RequirementCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    iteration_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Literal["todo", "in_progress", "review", "done", "closed"] = "todo"
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    assignee_id: Optional[UUID] = None
    requirement_id: Optional[UUID] = None
    iteration_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None


class BugCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    priority: Literal["low", "medium", "high", "critical"] = "medium"
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
    status: Optional[Literal["draft", "reviewing", "in_progress", "testing", "done", "closed"]] = None
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None
    assignee_id: Optional[UUID] = None
    iteration_id: Optional[UUID] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["todo", "in_progress", "review", "done", "closed"]] = None
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None
    assignee_id: Optional[UUID] = None
    iteration_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None


class BugUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    steps_to_reproduce: Optional[str] = None
    severity: Optional[Literal["low", "medium", "high", "critical"]] = None
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None
    status: Optional[Literal["open", "in_progress", "resolved", "closed"]] = None
    assignee_id: Optional[UUID] = None
    iteration_id: Optional[UUID] = None

class BoardCardCreate(BaseModel):
    column_id: UUID
    item_type: Literal["requirement", "task", "bug"]
    item_id: UUID
    order: int = 0

class BoardCardUpdate(BaseModel):
    column_id: Optional[UUID] = None
    order: Optional[int] = None
