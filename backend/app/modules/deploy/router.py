from __future__ import annotations
from typing import Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from app.core.pagination import normalize_pagination
from app.core.exceptions import NotFoundError
from app.modules.project.router import require_owner
from app.modules.artifact import models as artifact_models
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user, get_db, require_project_access
from app.modules.deploy import models as dm
from app.modules.deploy.schemas import DeployTaskCreate, EnvironmentCreate, K8sConfig, SshConfig
from app.modules.user.models import User

router = APIRouter(prefix="/api/v1/projects/{project_id}/deploy", tags=["deploy"], dependencies=[Depends(require_project_access)])


async def require_project_owner(project_id: UUID, user: User, db: AsyncSession) -> None:
    if user.is_superadmin:
        return
    await require_owner(project_id, user, db)

@router.post("/environments", status_code=status.HTTP_201_CREATED)
async def create_environment(project_id: UUID, payload: EnvironmentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    await require_project_owner(project_id, user, db)
    data = payload.model_dump()
    if payload.config is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Environment config is required")
    if payload.type == "ssh" and not isinstance(payload.config, SshConfig):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="SSH config required")
    if payload.type == "k8s" and not isinstance(payload.config, K8sConfig):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="K8s config required")
    data["config"] = payload.config.model_dump()
    env = dm.Environment(project_id=project_id, **data)
    db.add(env)
    await db.commit()
    await db.refresh(env)
    return {"id": env.id, "name": env.name, "type": env.type, "is_protected": env.is_protected}

@router.get("/environments", response_model=dict)
async def list_environments(project_id: UUID, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    normalized_page, normalized_page_size = normalize_pagination(page, page_size)
    stmt = select(dm.Environment).where(dm.Environment.project_id == project_id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (await db.scalars(stmt.order_by(dm.Environment.created_at.desc()).offset((normalized_page - 1) * normalized_page_size).limit(normalized_page_size))).all()
    return {"items": [{"id": r.id, "name": r.name, "type": r.type, "is_protected": r.is_protected} for r in rows], "meta": {"page": normalized_page, "page_size": normalized_page_size, "total": total}}

@router.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
async def create_deploy_task(project_id: UUID, payload: DeployTaskCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    await require_project_owner(project_id, user, db)
    env = await db.get(dm.Environment, payload.environment_id)
    if env is None or env.project_id != project_id:
        raise NotFoundError("Environment not found")
    if payload.artifact_id is not None:
        artifact = await db.get(artifact_models.Artifact, payload.artifact_id)
        if artifact is None:
            raise NotFoundError("Artifact not found")
        repository = await db.get(artifact_models.ArtifactRepository, artifact.repository_id)
        if repository is None or repository.project_id != project_id:
            raise NotFoundError("Artifact repository not found")
    task = dm.DeployTask(trigger_user_id=user.id, **payload.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return {"id": task.id, "environment_id": task.environment_id, "status": task.status}
