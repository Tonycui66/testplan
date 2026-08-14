from __future__ import annotations
import asyncio
import json
from datetime import datetime, timezone
import time
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.redis_client import get_redis
from app.dependencies import get_current_user, get_db, require_project_access
from app.modules.project.router import require_owner
from app.modules.pipeline import models as pm
from app.modules.pipeline.schemas import PipelineCreate, PipelineResponse, PipelineUpdate, RunCreate
from app.core.security import decode_access_token
from app.dependencies import get_session_factory
from app.modules.project.models import ProjectMember
from app.modules.user.models import User

router = APIRouter(prefix="/api/v1/projects/{project_id}/pipelines", tags=["pipeline"], dependencies=[Depends(require_project_access)])
ws_router = APIRouter(prefix="/api/v1/ws", tags=["pipeline-ws"])



async def require_owner_or_admin(project_id: UUID, user: User, db: AsyncSession) -> None:
    if user.is_superadmin:
        return
    member = await db.scalar(select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == user.id))
    if member is None or member.role not in {"owner", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner permission required")

async def get_pipeline(project_id: UUID, pipeline_id: UUID, db: AsyncSession) -> pm.Pipeline:
    pipeline = await db.scalar(select(pm.Pipeline).where(pm.Pipeline.id == pipeline_id, pm.Pipeline.project_id == project_id))
    if pipeline is None:
        raise NotFoundError("Pipeline not found")
    return pipeline


@router.post("", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(project_id: UUID, payload: PipelineCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> PipelineResponse:
    pipeline = pm.Pipeline(project_id=project_id, name=payload.name, description=payload.description)
    db.add(pipeline)
    await db.flush()
    for stage_input in payload.stages:
        stage = pm.PipelineStage(pipeline_id=pipeline.id, name=stage_input.name, order=stage_input.order, condition=stage_input.condition)
        db.add(stage)
        await db.flush()
        for job_input in stage_input.jobs:
            db.add(pm.PipelineJob(stage_id=stage.id, **job_input.model_dump()))
    await db.commit()
    await db.refresh(pipeline)
    return PipelineResponse.model_validate(pipeline)


@router.get("", response_model=dict)
async def list_pipelines(project_id: UUID, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    normalized_page = max(page, 1)
    normalized_size = min(max(page_size, 1), 100)
    stmt = select(pm.Pipeline).where(pm.Pipeline.project_id == project_id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (await db.scalars(stmt.order_by(pm.Pipeline.created_at.desc()).offset((normalized_page - 1) * normalized_size).limit(normalized_size))).all()
    return {"items": [PipelineResponse.model_validate(p).model_dump() for p in rows], "meta": {"page": normalized_page, "page_size": normalized_size, "total": total}}


@router.get("/{pipeline_id}", response_model=dict)
async def get_pipeline_detail(project_id: UUID, pipeline_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    pipeline = await get_pipeline(project_id, pipeline_id, db)
    stages = (await db.scalars(select(pm.PipelineStage).where(pm.PipelineStage.pipeline_id == pipeline.id).order_by(pm.PipelineStage.order))).all()
    detail: Dict[str, Any] = PipelineResponse.model_validate(pipeline).model_dump()
    detail["stages"] = []
    for stage in stages:
        jobs = (await db.scalars(select(pm.PipelineJob).where(pm.PipelineJob.stage_id == stage.id).order_by(pm.PipelineJob.order))).all()
        detail["stages"].append({
            "id": stage.id,
            "name": stage.name,
            "order": stage.order,
            "condition": stage.condition,
            "jobs": [
                {"id": j.id, "name": j.name, "image": j.image, "script": j.script, "timeout_seconds": j.timeout_seconds, "variables": j.variables}
                for j in jobs
            ],
        })
    return detail


@router.patch("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(project_id: UUID, pipeline_id: UUID, payload: PipelineUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> PipelineResponse:
    pipeline = await get_pipeline(project_id, pipeline_id, db)
    if payload.name is not None:
        pipeline.name = payload.name
    if payload.description is not None:
        pipeline.description = payload.description
    if payload.is_enabled is not None:
        pipeline.is_enabled = payload.is_enabled
    if payload.stages is not None:
        old_stages = (await db.scalars(select(pm.PipelineStage).where(pm.PipelineStage.pipeline_id == pipeline.id))).all()
        for old_stage in old_stages:
            old_jobs = (await db.scalars(select(pm.PipelineJob).where(pm.PipelineJob.stage_id == old_stage.id))).all()
            for old_job in old_jobs:
                await db.delete(old_job)
            await db.delete(old_stage)
        await db.flush()
        for stage_input in payload.stages:
            stage = pm.PipelineStage(pipeline_id=pipeline.id, name=stage_input.name, order=stage_input.order, condition=stage_input.condition)
            db.add(stage)
            await db.flush()
            for job_input in stage_input.jobs:
                db.add(pm.PipelineJob(stage_id=stage.id, **job_input.model_dump()))
    await db.commit()
    await db.refresh(pipeline)
    return PipelineResponse.model_validate(pipeline)


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(project_id: UUID, pipeline_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    await require_owner(project_id, user, db)
    pipeline = await get_pipeline(project_id, pipeline_id, db)
    await db.delete(pipeline)
    await db.commit()


@router.post("/{pipeline_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def trigger_run(project_id: UUID, pipeline_id: UUID, payload: RunCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    await require_owner_or_admin(project_id, user, db)
    pipeline = await get_pipeline(project_id, pipeline_id, db)
    if not pipeline.is_enabled:
        raise ConflictError("Pipeline is disabled")
    run_number = await db.scalar(
        text("UPDATE pipeline.pipelines SET run_counter = run_counter + 1 WHERE id = :id RETURNING run_counter"),
        {"id": pipeline.id},
    )
    run = pm.PipelineRun(
        pipeline_id=pipeline.id,
        run_number=int(run_number or pipeline.run_counter + 1),
        trigger_type=payload.trigger_type,
        trigger_user_id=user.id,
        branch=payload.branch,
        commit_sha=payload.commit_sha,
        variables=payload.variables,
        status="pending",
    )
    db.add(run)
    await db.flush()
    stages = (await db.scalars(select(pm.PipelineStage).where(pm.PipelineStage.pipeline_id == pipeline.id).order_by(pm.PipelineStage.order))).all()
    job_run_ids: Dict[str, UUID] = {}
    for stage in stages:
        stage_run = pm.StageRun(run_id=run.id, stage_id=stage.id, name=stage.name, status="pending", order=stage.order)
        db.add(stage_run)
        await db.flush()
        jobs = (await db.scalars(select(pm.PipelineJob).where(pm.PipelineJob.stage_id == stage.id).order_by(pm.PipelineJob.order))).all()
        for job in jobs:
            job_run = pm.JobRun(stage_run_id=stage_run.id, job_id=job.id, name=job.name, status="pending")
            db.add(job_run)
            await db.flush()
            job_run_ids[str(job.id)] = job_run.id
    await db.commit()
    redis = get_redis()
    try:
        await redis.rpush("queue:pipeline", json.dumps({"run_id": str(run.id), "job_run_ids": {str(k): str(v) for k, v in job_run_ids.items()}}))
    except Exception:
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        await db.commit()
        return {"id": run.id, "pipeline_id": pipeline.id, "run_number": run.run_number, "status": run.status}
    return {"id": run.id, "pipeline_id": pipeline.id, "run_number": run.run_number, "status": run.status}


@router.get("/{pipeline_id}/runs", response_model=dict)
async def list_runs(project_id: UUID, pipeline_id: UUID, page: int = 1, page_size: int = 20, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    pipeline = await get_pipeline(project_id, pipeline_id, db)
    normalized_page = max(page, 1)
    normalized_size = min(max(page_size, 1), 100)
    stmt = select(pm.PipelineRun).where(pm.PipelineRun.pipeline_id == pipeline.id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (await db.scalars(stmt.order_by(pm.PipelineRun.run_number.desc()).offset((normalized_page - 1) * normalized_size).limit(normalized_size))).all()
    return {"items": [{"id": r.id, "run_number": r.run_number, "status": r.status, "started_at": r.started_at, "finished_at": r.finished_at} for r in rows], "meta": {"page": normalized_page, "page_size": normalized_size, "total": total}}


@router.get("/{pipeline_id}/runs/{run_id}")
async def get_run(project_id: UUID, pipeline_id: UUID, run_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> Dict[str, Any]:
    pipeline = await get_pipeline(project_id, pipeline_id, db)
    run = await db.scalar(select(pm.PipelineRun).where(pm.PipelineRun.id == run_id, pm.PipelineRun.pipeline_id == pipeline.id))
    if run is None:
        raise NotFoundError("Pipeline run not found")
    stages = (await db.scalars(select(pm.StageRun).where(pm.StageRun.run_id == run.id).order_by(pm.StageRun.order))).all()
    return {"id": run.id, "run_number": run.run_number, "status": run.status, "stages": [{"id": s.id, "name": s.name, "status": s.status} for s in stages]}


@router.post("/{pipeline_id}/runs/{run_id}/cancel", response_model=dict)
async def cancel_run(project_id: UUID, pipeline_id: UUID, run_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    await require_owner_or_admin(project_id, user, db)
    pipeline = await get_pipeline(project_id, pipeline_id, db)
    run = await db.scalar(select(pm.PipelineRun).where(pm.PipelineRun.id == run_id, pm.PipelineRun.pipeline_id == pipeline.id))
    if run is None:
        raise NotFoundError("Pipeline run not found")
    if run.status not in {"pending", "running"}:
        raise ConflictError("Run is already finished")
    run.status = "cancelled"
    run.finished_at = datetime.now(timezone.utc)
    await mark_run_cancelled(db, run.id)
    return {"id": run.id, "status": run.status}



async def mark_run_cancelled(db: AsyncSession, run_id: UUID) -> None:
    stage_runs = (await db.scalars(select(pm.StageRun).where(pm.StageRun.run_id == run_id))).all()
    for stage_run in stage_runs:
        if stage_run.status not in {"success", "failed", "cancelled", "skipped"}:
            stage_run.status = "cancelled"
            stage_run.finished_at = datetime.now(timezone.utc)
    job_runs = (await db.scalars(select(pm.JobRun).join(pm.StageRun, pm.JobRun.stage_run_id == pm.StageRun.id).where(pm.StageRun.run_id == run_id))).all()
    for job_run in job_runs:
        if job_run.status not in {"success", "failed", "cancelled", "skipped"}:
            job_run.status = "cancelled"
            job_run.finished_at = datetime.now(timezone.utc)
    await db.commit()

@ws_router.websocket("/pipelines/{pipeline_id}/runs/{run_id}/logs")
async def pipeline_logs(websocket: WebSocket, pipeline_id: UUID, run_id: UUID) -> None:
    token = websocket.query_params.get("token") or websocket.headers.get("authorization", "").removeprefix("Bearer ")
    subject = decode_access_token(token) if token else None
    if not subject:
        await websocket.close(code=1008)
        return
    session_factory = get_session_factory()
    async with session_factory() as db:
        run = await db.get(pm.PipelineRun, run_id)
        if run is None or run.pipeline_id != pipeline_id:
            await websocket.close(code=1008)
            return
        pipeline = await db.get(pm.Pipeline, run.pipeline_id)
        if pipeline is None:
            await websocket.close(code=1008)
            return
        member = await db.scalar(select(ProjectMember).where(ProjectMember.project_id == pipeline.project_id, ProjectMember.user_id == UUID(subject)))
        current_user = await db.get(User, UUID(subject))
        if member is None and (current_user is None or not current_user.is_superadmin):
            await websocket.close(code=1008)
            return
    await websocket.accept()
    redis = get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"logs:{run_id}")
    async with session_factory() as db:
        history = (await db.scalars(
            select(pm.JobLog)
            .join(pm.JobRun, pm.JobLog.job_run_id == pm.JobRun.id)
            .join(pm.StageRun, pm.JobRun.stage_run_id == pm.StageRun.id)
            .join(pm.PipelineJob, pm.PipelineJob.id == pm.JobRun.job_id)
            .where(pm.StageRun.run_id == run_id)
            .order_by(pm.StageRun.order, pm.PipelineJob.order, pm.JobLog.line_number, pm.JobLog.timestamp, pm.JobLog.id)
        )).all()
        for log in history:
            await websocket.send_text(json.dumps({"id": str(log.id), "stream": log.stream, "content": log.content, "timestamp": log.timestamp.isoformat()}))
    while True:
        buffered = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0)
        if buffered is None:
            break
        if buffered.get("type") == "message":
            await websocket.send_text(buffered["data"])
    last_heartbeat = time.monotonic()
    last_client = time.monotonic()
    try:
        while True:
            now = time.monotonic()
            if now - last_heartbeat >= 30:
                await websocket.send_text("pong")
                last_heartbeat = now
            if now - last_client >= 300:
                await websocket.close(code=1001)
                break
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.25)
            if message and message.get("type") == "message":
                await websocket.send_text(message["data"])
            try:
                client_message = await asyncio.wait_for(websocket.receive_text(), timeout=0.25)
                last_client = time.monotonic()
                if client_message == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                continue
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"logs:{run_id}")
        await pubsub.close()
