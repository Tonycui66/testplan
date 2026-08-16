from __future__ import annotations
from typing import Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user, get_db, require_project_access
from app.modules.deploy import models as dm
from app.modules.deploy.schemas import DeployTaskCreate, EnvironmentCreate
from app.modules.user.models import User

router = APIRouter(prefix="/api/v1/projects/{project_id}/deploy", tags=["deploy"], dependencies=[Depends(require_project_access)])

@router.post("/environments", status_code=status.HTTP_201_CREATED)
async def create_environment(project_id: UUID, payload: EnvironmentCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    env = dm.Environment(project_id=project_id, **payload.model_dump())
    db.add(env)
    await db.commit()
    await db.refresh(env)
    return {"id": env.id, "name": env.name, "type": env.type, "is_protected": env.is_protected}

@router.get("/environments", response_model=dict)
async def list_environments(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    rows = (await db.scalars(select(dm.Environment).where(dm.Environment.project_id == project_id))).all()
    return {"items": [{"id": r.id, "name": r.name, "type": r.type, "is_protected": r.is_protected} for r in rows], "meta": {"total": len(rows)}}

@router.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
async def create_deploy_task(project_id: UUID, payload: DeployTaskCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    env = await db.get(dm.Environment, payload.environment_id)
    if env is None or env.project_id != project_id:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Environment not found")
    task = dm.DeployTask(trigger_user_id=user.id, **payload.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return {"id": task.id, "environment_id": task.environment_id, "status": task.status}
