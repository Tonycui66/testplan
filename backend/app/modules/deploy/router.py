from __future__ import annotations
from typing import Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
import json
from app.core.redis_client import get_redis
from sqlalchemy import func, select
from app.core.pagination import normalize_pagination
from app.core.exceptions import NotFoundError
from app.modules.project.router import require_owner
from app.modules.artifact import models as artifact_models
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user, get_db, require_project_access
from app.modules.deploy import models as dm
from app.modules.deploy.schemas import DeployTaskCreate, EnvironmentCreate, EnvironmentUpdate, K8sConfig, SshConfig, SshCredentialCreate
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
    try:
        await get_redis().rpush("queue:deploy", json.dumps({"task_id": str(task.id)}))
    except Exception:
        task.status = "failed"
        task.finished_at = datetime.now(timezone.utc)
        await db.commit()
    return {"id": task.id, "environment_id": task.environment_id, "status": task.status}

@router.patch("/environments/{environment_id}")
async def update_environment(project_id: UUID, environment_id: UUID, payload: EnvironmentUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    await require_project_owner(project_id, user, db)
    env = await db.get(dm.Environment, environment_id)
    if env is None or env.project_id != project_id:
        raise NotFoundError("Environment not found")
    if payload.name is not None:
        env.name = payload.name
    if payload.is_protected is not None:
        env.is_protected = payload.is_protected
    await db.commit()
    return {"id": env.id, "name": env.name, "is_protected": env.is_protected}


@router.delete("/environments/{environment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_environment(project_id: UUID, environment_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    await require_project_owner(project_id, user, db)
    env = await db.get(dm.Environment, environment_id)
    if env is None or env.project_id != project_id:
        raise NotFoundError("Environment not found")
    await db.delete(env)
    await db.commit()


@router.get("/tasks", response_model=dict)
async def list_tasks(project_id: UUID, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    env_ids = [e.id for e in (await db.scalars(select(dm.Environment).where(dm.Environment.project_id == project_id))).all()]
    if not env_ids:
        return {"items": [], "meta": {"page": max(page, 1), "page_size": min(max(page_size, 1), 100), "total": 0}}
    normalized_page, normalized_page_size = normalize_pagination(page, page_size)
    stmt = select(dm.DeployTask).where(dm.DeployTask.environment_id.in_(env_ids))
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (await db.scalars(stmt.order_by(dm.DeployTask.started_at.desc()).offset((normalized_page - 1) * normalized_page_size).limit(normalized_page_size))).all()
    return {"items": [{"id": t.id, "environment_id": t.environment_id, "status": t.status} for t in rows], "meta": {"page": normalized_page, "page_size": normalized_page_size, "total": total}}


@router.get("/tasks/{task_id}")
async def get_task(project_id: UUID, task_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    task = await db.get(dm.DeployTask, task_id)
    env = await db.get(dm.Environment, task.environment_id) if task else None
    if task is None or env is None or env.project_id != project_id:
        raise NotFoundError("Deploy task not found")
    return {"id": task.id, "environment_id": task.environment_id, "status": task.status, "strategy": task.strategy}


@router.post("/tasks/{task_id}/cancel", response_model=dict)
async def cancel_task(project_id: UUID, task_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    await require_project_owner(project_id, user, db)
    task = await db.get(dm.DeployTask, task_id)
    env = await db.get(dm.Environment, task.environment_id) if task else None
    if task is None or env is None or env.project_id != project_id:
        raise NotFoundError("Deploy task not found")
    task.status = "cancelled"
    task.finished_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": task.id, "status": task.status}


@router.post("/credentials", status_code=status.HTTP_201_CREATED)
async def create_credential(project_id: UUID, payload: SshCredentialCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    await require_project_owner(project_id, user, db)
    credential = dm.SshCredential(project_id=project_id, name=payload.name, host=payload.host, port=payload.port, username=payload.username, private_key_encrypted=payload.credential_ref)
    db.add(credential)
    await db.commit()
    await db.refresh(credential)
    return {"id": credential.id, "name": credential.name}


@router.delete("/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(project_id: UUID, credential_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    await require_project_owner(project_id, user, db)
    credential = await db.scalar(select(dm.SshCredential).where(dm.SshCredential.id == credential_id, dm.SshCredential.project_id == project_id))
    if credential is None:
        raise NotFoundError("Credential not found")
    await db.delete(credential)
    await db.commit()
