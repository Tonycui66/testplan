from __future__ import annotations
from typing import Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from app.core.pagination import normalize_pagination
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
async def list_repositories(project_id: UUID, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    normalized_page, normalized_page_size = normalize_pagination(page, page_size)
    stmt = select(am.ArtifactRepository).where(am.ArtifactRepository.project_id == project_id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (await db.scalars(stmt.order_by(am.ArtifactRepository.created_at.desc()).offset((normalized_page - 1) * normalized_page_size).limit(normalized_page_size))).all()
    return {"items": [{"id": r.id, "name": r.name, "type": r.type} for r in rows], "meta": {"page": normalized_page, "page_size": normalized_page_size, "total": total}}

@router.get("/repositories/{repository_id}/artifacts", response_model=dict)
async def list_artifacts(project_id: UUID, repository_id: UUID, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    repo = await db.get(am.ArtifactRepository, repository_id)
    if repo is None or repo.project_id != project_id:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Artifact repository not found")
    normalized_page, normalized_page_size = normalize_pagination(page, page_size)
    stmt = select(am.Artifact).where(am.Artifact.repository_id == repository_id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (await db.scalars(stmt.order_by(am.Artifact.name, am.Artifact.version).offset((normalized_page - 1) * normalized_page_size).limit(normalized_page_size))).all()
    return {"items": [{"id": r.id, "name": r.name, "version": r.version, "size_bytes": r.size_bytes, "storage_path": r.storage_path} for r in rows], "meta": {"page": normalized_page, "page_size": normalized_page_size, "total": total}}


@router.get("/repositories/{repository_id}/artifacts/{artifact_id}/download")
async def download_artifact(project_id: UUID, repository_id: UUID, artifact_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    repo = await db.get(am.ArtifactRepository, repository_id)
    if repo is None or repo.project_id != project_id:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Artifact repository not found")
    artifact = await db.get(am.Artifact, artifact_id)
    if artifact is None or artifact.repository_id != repository_id:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Artifact not found")
    return {"id": artifact.id, "name": artifact.name, "version": artifact.version, "storage_path": artifact.storage_path}


@router.post("/repositories/{repository_id}/artifacts", status_code=status.HTTP_201_CREATED)
async def upload_artifact(project_id: UUID, repository_id: UUID, payload: ArtifactCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    repo = await db.get(am.ArtifactRepository, repository_id)
    if repo is None or repo.project_id != project_id:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Artifact repository not found")
    data = payload.model_dump()
    metadata = data.pop("metadata", {})
    storage_path = f"{project_id}/{repository_id}/{data['name']}/{data['version']}"
    artifact = am.Artifact(repository_id=repository_id, storage_path=storage_path, artifact_metadata=metadata, **data)
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)
    return {"id": artifact.id, "name": artifact.name, "version": artifact.version, "storage_path": artifact.storage_path}
