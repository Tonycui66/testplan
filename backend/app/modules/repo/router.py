from __future__ import annotations
import secrets
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.dependencies import get_current_user, get_db, require_project_access
from app.modules.repo import models as rm
from app.modules.repo.schemas import RepoConnectionCreate, RepoConnectionResponse, WebhookEventCreate
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
async def list_connections(project_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    rows = (await db.scalars(select(rm.RepoConnection).where(rm.RepoConnection.project_id == project_id))).all()
    return {"items": [RepoConnectionResponse.model_validate(c).model_dump() for c in rows]}


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(project_id: UUID, connection_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> None:
    connection = await get_connection(project_id, connection_id, db)
    connection.is_active = False
    await db.commit()


@router.get("/branches", response_model=dict)
async def list_branches(project_id: UUID, connection_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    await get_connection(project_id, connection_id, db)
    rows = (await db.scalars(select(rm.Branch).where(rm.Branch.connection_id == connection_id))).all()
    return {"items": [{"id": b.id, "name": b.name, "last_commit_sha": b.last_commit_sha} for b in rows]}


@router.get("/commits", response_model=dict)
async def list_commits(project_id: UUID, connection_id: UUID, branch: Optional[str] = None, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    await get_connection(project_id, connection_id, db)
    stmt = select(rm.Commit).where(rm.Commit.connection_id == connection_id)
    if branch:
        stmt = stmt.where(rm.Commit.branch == branch)
    rows = (await db.scalars(stmt.order_by(rm.Commit.committed_at.desc()).limit(100))).all()
    return {"items": [{"id": c.id, "sha": c.sha, "message": c.message, "branch": c.branch, "committed_at": c.committed_at} for c in rows]}


@webhook_router.post("/{provider}", status_code=status.HTTP_202_ACCEPTED)
async def receive_webhook(provider: str, payload: WebhookEventCreate, request: Request, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    connection_id = payload.payload.get("connection_id")
    if not connection_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="connection_id is required")
    event = rm.WebhookEvent(connection_id=UUID(str(connection_id)), event_type=payload.event_type, payload=payload.payload, processed=False)
    db.add(event)
    await db.commit()
    return {"id": event.id, "event_type": event.event_type, "processed": event.processed}
