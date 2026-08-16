import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.logging_config import configure_logging
from app.core.redis_client import get_redis
from app.dependencies import get_database_engine
from app.modules.deploy import models as dm
from app.modules.pipeline import models as pm


TERMINAL = {"success", "failed", "cancelled", "skipped"}


async def publish_log(redis, run_id: str, stream: str, content: str, db=None, job_run_id=None) -> None:
    timestamp = datetime.now(timezone.utc)
    log_id = None
    if db is not None and job_run_id is not None:
        next_line = await db.scalar(select(func.coalesce(func.max(pm.JobLog.line_number), 0) + 1).where(pm.JobLog.job_run_id == job_run_id)) or 1
        log = pm.JobLog(job_run_id=job_run_id, line_number=next_line, content=content, stream=stream, timestamp=timestamp)
        db.add(log)
        await db.commit()
        await db.refresh(log)
        log_id = log.id
    line = json.dumps({"id": str(log_id) if log_id else None, "stream": stream, "content": content, "timestamp": timestamp.isoformat()})
    await redis.publish(f"logs:{run_id}", line)


async def mark_all_cancelled(db, run_id: UUID) -> None:
    stage_runs = (await db.scalars(select(pm.StageRun).where(pm.StageRun.run_id == run_id))).all()
    for stage_run in stage_runs:
        if stage_run.status not in TERMINAL:
            stage_run.status = "cancelled"
            stage_run.finished_at = datetime.now(timezone.utc)
    job_runs = (await db.scalars(
        select(pm.JobRun).join(pm.StageRun, pm.JobRun.stage_run_id == pm.StageRun.id).where(pm.StageRun.run_id == run_id)
    )).all()
    for job_run in job_runs:
        if job_run.status not in TERMINAL:
            job_run.status = "cancelled"
            job_run.finished_at = datetime.now(timezone.utc)
    await db.commit()


async def process_run(payload: Dict[str, Any]) -> None:
    session_factory = async_sessionmaker(get_database_engine(), expire_on_commit=False)
    redis = get_redis()
    async with session_factory() as db:
        run = await db.get(pm.PipelineRun, UUID(payload["run_id"]))
        if run is None or run.status in {"cancelled", "success", "failed"}:
            return
        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        await db.commit()

        stage_runs = (await db.scalars(select(pm.StageRun).where(pm.StageRun.run_id == run.id).order_by(pm.StageRun.order))).all()
        previous_status = "success"
        failed = False
        for stage_run in stage_runs:
            await db.refresh(run)
            if run.status == "cancelled":
                await mark_all_cancelled(db, run.id)
                return
            stage = await db.get(pm.PipelineStage, stage_run.stage_id)
            condition = stage.condition if stage else "always"
            should_run = condition == "always"
            if condition == "on_success" and previous_status == "success":
                should_run = True
            if condition == "on_failure" and previous_status == "failed":
                should_run = True

            if not should_run:
                stage_run.status = "skipped"
                stage_run.finished_at = datetime.now(timezone.utc)
                await db.commit()
                continue

            stage_run.status = "running"
            stage_run.started_at = datetime.now(timezone.utc)
            await db.commit()

            job_runs = (await db.scalars(
                select(pm.JobRun)
                .join(pm.PipelineJob, pm.PipelineJob.id == pm.JobRun.job_id)
                .where(pm.JobRun.stage_run_id == stage_run.id)
                .order_by(pm.PipelineJob.order)
            )).all()
            stage_failed = False
            for job_run in job_runs:
                await db.refresh(run)
                if run.status == "cancelled":
                    stage_run.status = "cancelled"
                    stage_run.finished_at = datetime.now(timezone.utc)
                    await db.commit()
                    await mark_all_cancelled(db, run.id)
                    return
                job_run.status = "running"
                job_run.started_at = datetime.now(timezone.utc)
                await db.commit()
                await publish_log(redis, str(run.id), "stdout", f"{job_run.name}: started", db, job_run.id)
                try:
                    await asyncio.sleep(0.1)
                    job_run.status = "success"
                    job_run.exit_code = 0
                    job_run.finished_at = datetime.now(timezone.utc)
                    await db.commit()
                    await publish_log(redis, str(run.id), "stdout", f"{job_run.name}: completed", db, job_run.id)
                except Exception:
                    job_run.status = "failed"
                    job_run.exit_code = 1
                    job_run.finished_at = datetime.now(timezone.utc)
                    stage_failed = True
                    failed = True
                    await db.commit()
                    await publish_log(redis, str(run.id), "stderr", f"{job_run.name}: failed", db, job_run.id)

            stage_run.status = "failed" if stage_failed else "success"
            stage_run.finished_at = datetime.now(timezone.utc)
            previous_status = stage_run.status
            await db.commit()

        await db.refresh(run)
        if run.status == "cancelled":
            await mark_all_cancelled(db, run.id)
            return
        run.status = "failed" if failed else "success"
        run.finished_at = datetime.now(timezone.utc)
        await db.commit()



async def process_deploy_task(task_id: str) -> None:
    session_factory = async_sessionmaker(get_database_engine(), expire_on_commit=False)
    async with session_factory() as db:
        task = await db.get(dm.DeployTask, UUID(task_id))
        if task is None or task.status not in {"pending", "running"}:
            return
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        await db.commit()
        await asyncio.sleep(0.1)
        await db.refresh(task)
        if task.status == "cancelled":
            return
        task.status = "success"
        task.finished_at = datetime.now(timezone.utc)
        await db.commit()


async def pop_job(redis):
    return await redis.blpop(("queue:pipeline", "queue:deploy"), timeout=1)


async def dispatch_job(redis, message) -> None:
    if message is None:
        return
    queue_name = message[0]
    if queue_name == "queue:pipeline":
        await process_run(json.loads(message[1]))
    elif queue_name == "queue:deploy":
        await process_deploy_task(json.loads(message[1]).get("task_id", ""))


async def consume_once(redis) -> bool:
    message = await pop_job(redis)
    if message is None:
        return False
    await dispatch_job(redis, message)
    return True


async def main() -> None:
    configure_logging()
    redis = get_redis()
    while True:
        try:
            await consume_once(redis)
        except Exception:
            continue


if __name__ == "__main__":
    asyncio.run(main())
