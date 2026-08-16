from __future__ import annotations
from typing import Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user, get_db, require_project_access
from app.modules.artifact import models as am
from app.modules.artifact.schemas import ArtifactCreate, RepositoryCreate
from app.modules.user.models import User

router = APIRouter(prefix="/api/v1/projects/{project_id}/artifacts", tags=["artifact"], dependencies=[Depends(require_project_access)])

@router.post("/repositories", status_code=status.HTTP_201_CREATED)
async def create_repository(project_id: UUID, payload: RepositoryCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    repo = am.ArtifactRepository(project_id=project_id, **payload.model_dump())
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    return {"id": repo.id, "name": repo.name, "type": repo.type}

@router.get("/repositories", response_model=dict)
async def list_repositories(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    rows = (await db.scalars(select(am.ArtifactRepository).where(am.ArtifactRepository.project_id == project_id))).all()
    return {"items": [{"id": r.id, "name": r.name, "type": r.type} for r in rows], "meta": {"total": len(rows)}}

@router.post("/repositories/{repository_id}/artifacts", status_code=status.HTTP_201_CREATED)
async def upload_artifact(project_id: UUID, repository_id: UUID, payload: ArtifactCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    repo = await db.get(am.ArtifactRepository, repository_id)
    if repo is None or repo.project_id != project_id:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Artifact repository not found")
    data = payload.model_dump()
    metadata = data.pop("metadata", {})
    artifact = am.Artifact(repository_id=repository_id, artifact_metadata=metadata, **data)
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)
    return {"id": artifact.id, "name": artifact.name, "version": artifact.version, "storage_path": artifact.storage_path}
