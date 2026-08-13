from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.dependencies import get_current_user, get_db
from app.modules.project import models as pm
from app.modules.project.schemas import (
    BoardColumnCreate,
    BoardColumnUpdate,
    BugCreate,
    IterationCreate,
    IterationUpdate,
    MemberCreate,
    MemberResponse,
    MemberUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    RequirementCreate,
    TaskCreate,
)
from app.modules.user.models import User

router = APIRouter(prefix="/api/v1/projects", tags=["project"])


def project_response(project: pm.Project) -> ProjectResponse:
    return ProjectResponse.model_validate(project)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> ProjectResponse:
    exists = await db.scalar(select(pm.Project).where(pm.Project.key == payload.key))
    if exists:
        raise ConflictError("Project key already exists")
    project = pm.Project(name=payload.name, key=payload.key, description=payload.description)
    db.add(project)
    await db.flush()
    member = pm.ProjectMember(project_id=project.id, user_id=user.id, role="owner")
    board = pm.Board(project_id=project.id, name="默认看板", type="kanban")
    db.add_all([member, board])
    await db.flush()
    await db.add_all(
        [
            pm.BoardColumn(board_id=board.id, name="待办", order=0),
            pm.BoardColumn(board_id=board.id, name="进行中", order=1),
            pm.BoardColumn(board_id=board.id, name="已完成", order=2),
        ]
    )
    await db.commit()
    await db.refresh(project)
    return project_response(project)


@router.get("", response_model=dict)
async def list_projects(page: int = 1, search: str = "", db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    stmt = select(pm.Project).where(pm.Project.deleted_at.is_(None))
    if search:
        stmt = stmt.where(pm.Project.name.ilike(f"%{search}%"))
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    offset = (max(page, 1) - 1) * min(max(20, 1), 100)
    projects = (await db.scalars(stmt.order_by(pm.Project.created_at.desc()).offset(offset).limit(20))).all()
    return {"items": [project_response(p).model_dump() for p in projects], "meta": {"page": page, "page_size": 20, "total": total}}


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> ProjectResponse:
    project = await db.get(pm.Project, project_id)
    if project is None or project.deleted_at is not None:
        raise NotFoundError("Project not found")
    return project_response(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: UUID, payload: ProjectUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> ProjectResponse:
    project = await db.get(pm.Project, project_id)
    if project is None or project.deleted_at is not None:
        raise NotFoundError("Project not found")
    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
    await db.commit()
    await db.refresh(project)
    return project_response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> None:
    project = await db.get(pm.Project, project_id)
    if project is None:
        raise NotFoundError("Project not found")
    project.deleted_at = func.now()
    await db.commit()


@router.get("/{project_id}/members", response_model=dict)
async def list_members(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    rows = (await db.scalars(select(pm.ProjectMember).where(pm.ProjectMember.project_id == project_id))).all()
    return {"items": [MemberResponse(user_id=row.user_id, role=row.role).model_dump() for row in rows]}


@router.post("/{project_id}/members", response_model=MemberResponse)
async def add_member(project_id: UUID, payload: MemberCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> MemberResponse:
    exists = await db.scalar(select(pm.ProjectMember).where(pm.ProjectMember.project_id == project_id, pm.ProjectMember.user_id == payload.user_id))
    if exists:
        raise ConflictError("User is already a project member")
    member = pm.ProjectMember(project_id=project_id, user_id=payload.user_id, role=payload.role)
    db.add(member)
    await db.commit()
    return MemberResponse(user_id=member.user_id, role=member.role)


@router.patch("/{project_id}/members/{user_id}", response_model=MemberResponse)
async def update_member(project_id: UUID, user_id: UUID, payload: MemberUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> MemberResponse:
    member = await db.scalar(select(pm.ProjectMember).where(pm.ProjectMember.project_id == project_id, pm.ProjectMember.user_id == user_id))
    if member is None:
        raise NotFoundError("Project member not found")
    member.role = payload.role
    await db.commit()
    return MemberResponse(user_id=member.user_id, role=member.role)


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(project_id: UUID, user_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> None:
    member = await db.scalar(select(pm.ProjectMember).where(pm.ProjectMember.project_id == project_id, pm.ProjectMember.user_id == user_id))
    if member is None:
        raise NotFoundError("Project member not found")
    await db.delete(member)
    await db.commit()


@router.post("/{project_id}/iterations", status_code=status.HTTP_201_CREATED)
async def create_iteration(project_id: UUID, payload: IterationCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    iteration = pm.Iteration(project_id=project_id, **payload.model_dump())
    db.add(iteration)
    await db.commit()
    await db.refresh(iteration)
    return {"id": iteration.id, "name": iteration.name, "start_date": iteration.start_date, "end_date": iteration.end_date}


@router.get("/{project_id}/iterations", response_model=dict)
async def list_iterations(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    rows = (await db.scalars(select(pm.Iteration).where(pm.Iteration.project_id == project_id, pm.Iteration.deleted_at.is_(None)))).all()
    return {"items": [{"id": r.id, "name": r.name, "status": r.status} for r in rows]}


@router.patch("/{project_id}/iterations/{iteration_id}")
async def update_iteration(project_id: UUID, iteration_id: UUID, payload: IterationUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    iteration = await db.get(pm.Iteration, iteration_id)
    if iteration is None or iteration.project_id != project_id:
        raise NotFoundError("Iteration not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(iteration, key, value)
    await db.commit()
    return {"id": iteration.id, "name": iteration.name, "status": iteration.status}


@router.delete("/{project_id}/iterations/{iteration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_iteration(project_id: UUID, iteration_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> None:
    iteration = await db.get(pm.Iteration, iteration_id)
    if iteration is None or iteration.project_id != project_id:
        raise NotFoundError("Iteration not found")
    iteration.deleted_at = func.now()
    await db.commit()


@router.post("/{project_id}/requirements", status_code=status.HTTP_201_CREATED)
async def create_requirement(project_id: UUID, payload: RequirementCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    requirement = pm.Requirement(project_id=project_id, **payload.model_dump())
    db.add(requirement)
    await db.commit()
    await db.refresh(requirement)
    return {"id": requirement.id, "title": requirement.title, "status": requirement.status, "priority": requirement.priority}


@router.get("/{project_id}/requirements", response_model=dict)
async def list_requirements(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    rows = (await db.scalars(select(pm.Requirement).where(pm.Requirement.project_id == project_id, pm.Requirement.deleted_at.is_(None)))).all()
    return {"items": [{"id": r.id, "title": r.title, "status": r.status, "priority": r.priority} for r in rows]}


@router.get("/{project_id}/requirements/{requirement_id}")
async def get_requirement(project_id: UUID, requirement_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    row = await db.get(pm.Requirement, requirement_id)
    if row is None or row.project_id != project_id:
        raise NotFoundError("Requirement not found")
    return {"id": row.id, "title": row.title, "description": row.description, "status": row.status, "priority": row.priority}


@router.patch("/{project_id}/requirements/{requirement_id}")
async def update_requirement(project_id: UUID, requirement_id: UUID, payload: RequirementCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    row = await db.get(pm.Requirement, requirement_id)
    if row is None or row.project_id != project_id:
        raise NotFoundError("Requirement not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    await db.commit()
    return {"id": row.id, "title": row.title, "status": row.status, "priority": row.priority}


@router.delete("/{project_id}/requirements/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(project_id: UUID, requirement_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> None:
    row = await db.get(pm.Requirement, requirement_id)
    if row is None or row.project_id != project_id:
        raise NotFoundError("Requirement not found")
    row.deleted_at = func.now()
    await db.commit()


@router.post("/{project_id}/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(project_id: UUID, payload: TaskCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    task = pm.Task(project_id=project_id, **payload.model_dump(exclude={"requirement_id"}))
    db.add(task)
    await db.flush()
    if payload.requirement_id:
        db.add(pm.RequirementTask(requirement_id=payload.requirement_id, task_id=task.id))
    await db.commit()
    return {"id": task.id, "title": task.title, "status": task.status, "priority": task.priority}


@router.get("/{project_id}/tasks", response_model=dict)
async def list_tasks(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    rows = (await db.scalars(select(pm.Task).where(pm.Task.project_id == project_id, pm.Task.deleted_at.is_(None)))).all()
    return {"items": [{"id": r.id, "title": r.title, "status": r.status, "priority": r.priority} for r in rows]}


@router.get("/{project_id}/tasks/{task_id}")
async def get_task(project_id: UUID, task_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    row = await db.get(pm.Task, task_id)
    if row is None or row.project_id != project_id:
        raise NotFoundError("Task not found")
    return {"id": row.id, "title": row.title, "description": row.description, "status": row.status, "priority": row.priority}


@router.patch("/{project_id}/tasks/{task_id}")
async def update_task(project_id: UUID, task_id: UUID, payload: TaskCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    row = await db.get(pm.Task, task_id)
    if row is None or row.project_id != project_id:
        raise NotFoundError("Task not found")
    for key, value in payload.model_dump(exclude_unset=True, exclude={"requirement_id"}).items():
        setattr(row, key, value)
    await db.commit()
    return {"id": row.id, "title": row.title, "status": row.status, "priority": row.priority}


@router.delete("/{project_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(project_id: UUID, task_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> None:
    row = await db.get(pm.Task, task_id)
    if row is None or row.project_id != project_id:
        raise NotFoundError("Task not found")
    row.deleted_at = func.now()
    await db.commit()


@router.post("/{project_id}/bugs", status_code=status.HTTP_201_CREATED)
async def create_bug(project_id: UUID, payload: BugCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    bug = pm.Bug(project_id=project_id, **payload.model_dump())
    db.add(bug)
    await db.commit()
    return {"id": bug.id, "title": bug.title, "severity": bug.severity, "status": bug.status}


@router.get("/{project_id}/bugs", response_model=dict)
async def list_bugs(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    rows = (await db.scalars(select(pm.Bug).where(pm.Bug.project_id == project_id, pm.Bug.deleted_at.is_(None)))).all()
    return {"items": [{"id": r.id, "title": r.title, "severity": r.severity, "status": r.status} for r in rows]}


@router.get("/{project_id}/bugs/{bug_id}")
async def get_bug(project_id: UUID, bug_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    row = await db.get(pm.Bug, bug_id)
    if row is None or row.project_id != project_id:
        raise NotFoundError("Bug not found")
    return {"id": row.id, "title": row.title, "severity": row.severity, "status": row.status}


@router.patch("/{project_id}/bugs/{bug_id}")
async def update_bug(project_id: UUID, bug_id: UUID, payload: BugCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    row = await db.get(pm.Bug, bug_id)
    if row is None or row.project_id != project_id:
        raise NotFoundError("Bug not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    await db.commit()
    return {"id": row.id, "title": row.title, "severity": row.severity, "status": row.status}


@router.delete("/{project_id}/bugs/{bug_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bug(project_id: UUID, bug_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> None:
    row = await db.get(pm.Bug, bug_id)
    if row is None or row.project_id != project_id:
        raise NotFoundError("Bug not found")
    row.deleted_at = func.now()
    await db.commit()


@router.get("/{project_id}/board", response_model=dict)
async def get_board(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    board = await db.scalar(select(pm.Board).where(pm.Board.project_id == project_id))
    if board is None:
        raise NotFoundError("Board not found")
    columns = (await db.scalars(select(pm.BoardColumn).where(pm.BoardColumn.board_id == board.id).order_by(pm.BoardColumn.order))).all()
    cards = (await db.scalars(select(pm.BoardCard).where(pm.BoardCard.board_id == board.id).order_by(pm.BoardCard.order))).all()
    return {
        "columns": [{"id": c.id, "name": c.name, "order": c.order} for c in columns],
        "cards": [{"id": c.id, "column_id": c.column_id, "item_type": c.item_type, "item_id": c.item_id} for c in cards],
    }


@router.post("/{project_id}/board/columns", status_code=status.HTTP_201_CREATED)
async def create_board_column(project_id: UUID, payload: BoardColumnCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    board = await db.scalar(select(pm.Board).where(pm.Board.project_id == project_id))
    if board is None:
        raise NotFoundError("Board not found")
    column = pm.BoardColumn(board_id=board.id, name=payload.name, order=payload.order)
    db.add(column)
    await db.commit()
    return {"id": column.id, "name": column.name, "order": column.order}


@router.patch("/{project_id}/board/columns/{column_id}")
async def update_board_column(project_id: UUID, column_id: UUID, payload: BoardColumnUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, Any]:
    column = await db.get(pm.BoardColumn, column_id)
    if column is None:
        raise NotFoundError("Board column not found")
    if payload.name is not None:
        column.name = payload.name
    if payload.order is not None:
        column.order = payload.order
    await db.commit()
    return {"id": column.id, "name": column.name, "order": column.order}
