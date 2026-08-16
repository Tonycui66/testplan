from __future__ import annotations

import json
import mimetypes
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import normalize_pagination
from app.dependencies import get_current_user, get_db, require_project_access
from app.modules.artifact import models as am
from app.modules.artifact.schemas import ArtifactCreate, RepositoryCreate
from app.modules.artifact.storage import LocalArtifactStorage, get_artifact_storage
from app.modules.project.router import require_owner
from app.modules.user.models import User

router = APIRouter(prefix="/api/v1/projects/{project_id}/artifacts", tags=["artifact"], dependencies=[Depends(require_project_access)])

def _parse_metadata(raw_metadata: str) -> Dict[str, Any]:
    if len(raw_metadata.encode("utf-8")) > 64 * 1024:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Artifact metadata is too large")
    try:
        metadata = json.loads(raw_metadata or "{}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Artifact metadata must be valid JSON")
    if not isinstance(metadata, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Artifact metadata must be a JSON object")
    return metadata


@router.post("/repositories", status_code=status.HTTP_201_CREATED)
async def create_repository(project_id: UUID, payload: RepositoryCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    await require_owner(project_id, user, db)
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
        raise NotFoundError("Artifact repository not found")
    normalized_page, normalized_page_size = normalize_pagination(page, page_size)
    stmt = select(am.Artifact).where(am.Artifact.repository_id == repository_id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (await db.scalars(stmt.order_by(am.Artifact.name, am.Artifact.version).offset((normalized_page - 1) * normalized_page_size).limit(normalized_page_size))).all()
    return {"items": [{"id": r.id, "name": r.name, "version": r.version, "size_bytes": r.size_bytes, "checksum": r.checksum} for r in rows], "meta": {"page": normalized_page, "page_size": normalized_page_size, "total": total}}


@router.get("/repositories/{repository_id}/artifacts/{artifact_id}/download")
async def download_artifact(project_id: UUID, repository_id: UUID, artifact_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user), storage: LocalArtifactStorage = Depends(get_artifact_storage)) -> FileResponse:
    repo = await db.get(am.ArtifactRepository, repository_id)
    if repo is None or repo.project_id != project_id:
        raise NotFoundError("Artifact repository not found")
    artifact = await db.get(am.Artifact, artifact_id)
    if artifact is None or artifact.repository_id != repository_id:
        raise NotFoundError("Artifact not found")
    path = storage.resolve(artifact.storage_path)
    media_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    filename = f"{artifact.name}-{artifact.version}{path.suffix}"
    return FileResponse(path=path, media_type=media_type, filename=filename)


@router.post("/repositories/{repository_id}/artifacts", status_code=status.HTTP_201_CREATED)
async def upload_artifact(
    project_id: UUID,
    repository_id: UUID,
    file: UploadFile = File(...),
    name: str = Form(...),
    version: str = Form(...),
    metadata: str = Form("{}"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    storage: LocalArtifactStorage = Depends(get_artifact_storage),
) -> Dict[str, Any]:
    repo = await db.get(am.ArtifactRepository, repository_id)
    if repo is None or repo.project_id != project_id:
        raise NotFoundError("Artifact repository not found")
    await require_owner(project_id, user, db)
    metadata_dict = _parse_metadata(metadata)
    try:
        payload = ArtifactCreate(name=name, version=version, metadata=metadata_dict)
    except ValidationError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid artifact name, version, or metadata")

    try:
        stored = await storage.save(file, project_id, repository_id)
    finally:
        await file.close()

    artifact = am.Artifact(
        repository_id=repository_id,
        name=payload.name,
        version=payload.version,
        size_bytes=stored.size_bytes,
        storage_path=stored.storage_path,
        checksum=stored.checksum,
        artifact_metadata=payload.metadata,
    )
    db.add(artifact)
    try:
        await db.commit()
    except Exception:
        await storage.delete(stored.storage_path)
        raise
    await db.refresh(artifact)
    return {"id": artifact.id, "name": artifact.name, "version": artifact.version, "size_bytes": artifact.size_bytes, "checksum": artifact.checksum, "content_type": stored.content_type}
