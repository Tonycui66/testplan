from __future__ import annotations
import hashlib
import hmac
import json
import secrets
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.pagination import normalize_pagination
from app.dependencies import get_current_user, get_db, require_project_access
from app.modules.project.router import require_owner
from app.modules.repo import models as rm
from app.modules.repo.schemas import RepoConnectionCreate, RepoConnectionResponse, WebhookEventCreate
from app.core.redis_client import get_redis
from app.modules.user.models import User

router = APIRouter(prefix="/api/v1/projects/{project_id}/repo", tags=["repo"], dependencies=[Depends(require_project_access)])
webhook_router = APIRouter(prefix="/api/v1/webhooks", tags=["repo-webhook"])


async def get_connection(project_id: UUID, connection_id: UUID, db: AsyncSession) -> rm.RepoConnection:
    connection = await db.scalar(select(rm.RepoConnection).where(rm.RepoConnection.id == connection_id, rm.RepoConnection.project_id == project_id))
    if connection is None:
        raise NotFoundError("Repo connection not found")
    return connection


@router.post("/connections", response_model=RepoConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(project_id: UUID, payload: RepoConnectionCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> RepoConnectionResponse:
    connection = rm.RepoConnection(project_id=project_id, **payload.model_dump(), webhook_secret=secrets.token_hex(32))
    db.add(connection)
    await db.commit()
    await db.refresh(connection)
    return RepoConnectionResponse.model_validate(connection)


@router.get("/connections", response_model=dict)
async def list_connections(project_id: UUID, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    normalized_page, normalized_page_size = normalize_pagination(page, page_size)
    stmt = select(rm.RepoConnection).where(rm.RepoConnection.project_id == project_id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (await db.scalars(stmt.order_by(rm.RepoConnection.created_at.desc()).offset((normalized_page - 1) * normalized_page_size).limit(normalized_page_size))).all()
    return {"items": [RepoConnectionResponse.model_validate(c).model_dump() for c in rows], "meta": {"page": normalized_page, "page_size": normalized_page_size, "total": total}}


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(project_id: UUID, connection_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    await require_owner(project_id, user, db)
    connection = await get_connection(project_id, connection_id, db)
    connection.is_active = False
    await db.commit()


@router.get("/branches", response_model=dict)
async def list_branches(project_id: UUID, connection_id: UUID, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    await get_connection(project_id, connection_id, db)
    normalized_page, normalized_page_size = normalize_pagination(page, page_size)
    stmt = select(rm.Branch).where(rm.Branch.connection_id == connection_id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (await db.scalars(stmt.order_by(rm.Branch.name).offset((normalized_page - 1) * normalized_page_size).limit(normalized_page_size))).all()
    return {"items": [{"id": b.id, "name": b.name, "last_commit_sha": b.last_commit_sha} for b in rows], "meta": {"page": normalized_page, "page_size": normalized_page_size, "total": total}}


@router.get("/commits", response_model=dict)
async def list_commits(project_id: UUID, connection_id: UUID, branch: Optional[str] = None, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    await get_connection(project_id, connection_id, db)
    normalized_page, normalized_page_size = normalize_pagination(page, page_size)
    stmt = select(rm.Commit).where(rm.Commit.connection_id == connection_id)
    if branch:
        stmt = stmt.where(rm.Commit.branch == branch)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (await db.scalars(stmt.order_by(rm.Commit.committed_at.desc()).offset((normalized_page - 1) * normalized_page_size).limit(normalized_page_size))).all()
    return {"items": [{"id": c.id, "sha": c.sha, "message": c.message, "branch": c.branch, "committed_at": c.committed_at} for c in rows], "meta": {"page": normalized_page, "page_size": normalized_page_size, "total": total}}


@webhook_router.post("/{provider}", status_code=status.HTTP_202_ACCEPTED)
async def receive_webhook(provider: str, payload: WebhookEventCreate, request: Request, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    if provider not in {"github", "gitlab"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported provider")
    connection_id_value = payload.payload.get("connection_id")
    if not connection_id_value:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="connection_id is required")
    try:
        connection_id = UUID(str(connection_id_value))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="connection_id must be a UUID")
    connection = await db.get(rm.RepoConnection, connection_id)
    if connection is None or not connection.is_active or not connection.webhook_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook target")
    raw_body = await request.body()
    header_names = ["x-hub-signature-256", "x-gitlab-token", "x-signature"]
    signature = next((request.headers.get(name, "") for name in header_names if request.headers.get(name)), "")
    if signature.startswith("sha256="):
        expected = hmac.new(connection.webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(f"sha256={expected}", signature):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook signature")
    else:
        expected = hmac.new(connection.webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook signature")
    dedupe_key = request.headers.get("x-github-delivery") or request.headers.get("x-gitlab-event-uuid") or request.headers.get("x-webhook-id") or hashlib.sha256(raw_body).hexdigest()
    existing = await db.scalar(select(rm.WebhookEvent).where(rm.WebhookEvent.connection_id == connection.id, rm.WebhookEvent.dedupe_key == dedupe_key))
    if existing is not None:
        return {"id": existing.id, "event_type": existing.event_type, "processed": existing.processed, "queued": True, "duplicate": True}
    event = rm.WebhookEvent(connection_id=connection.id, event_type=payload.event_type, payload=payload.payload, processed=False, dedupe_key=dedupe_key)
    db.add(event)
    await db.commit()
    queued = True
    try:
        await get_redis().rpush("queue:webhook", json.dumps({"event_id": str(event.id), "connection_id": str(connection.id), "payload": payload.payload}))
    except Exception as exc:
        queued = False
        event.payload = {**event.payload, "enqueue_error": str(exc)}
        await db.commit()
    return {"id": event.id, "event_type": event.event_type, "processed": event.processed, "queued": queued}
