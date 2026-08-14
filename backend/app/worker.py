import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.logging_config import configure_logging
from app.core.redis_client import get_redis
from app.dependencies import get_database_engine
from app.modules.pipeline import models as pm


async def publish_log(redis, run_id: str, stream: str, content: str) -> None:
    line = json.dumps({"stream": stream, "content": content, "timestamp": datetime.now(timezone.utc).isoformat()})
    await redis.publish(f"logs:{run_id}", line)


async def fail_run(db, run, stage_run=None, job_run=None, message="failed") -> None:
    if stage_run is not None and stage_run.status not in {"success", "failed", "cancelled"}:
        stage_run.status = "failed"
        stage_run.finished_at = datetime.now(timezone.utc)
    if job_run is not None and job_run.status not in {"success", "failed", "cancelled"}:
        job_run.status = "failed"
        job_run.exit_code = 1
        job_run.finished_at = datetime.now(timezone.utc)
    if run.status not in {"failed", "cancelled"}:
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
    await db.commit()


async def process_run(payload: Dict[str, Any]) -> None:
    session_factory = async_sessionmaker(get_database_engine(), expire_on_commit=False)
    redis = get_redis()
    async with session_factory() as db:
        run = await db.get(pm.PipelineRun, UUID(payload["run_id"]))
        if run is None or run.status == "cancelled":
            return
        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        await db.commit()

        stage_runs = (await db.scalars(select(pm.StageRun).where(pm.StageRun.run_id == run.id).order_by(pm.StageRun.order))).all()
        for stage_run in stage_runs:
            await db.refresh(run)
            if run.status == "cancelled":
                return
            stage_run.status = "running"
            stage_run.started_at = datetime.now(timezone.utc)
            await db.commit()
            job_runs = (await db.scalars(select(pm.JobRun).where(pm.JobRun.stage_run_id == stage_run.id).order_by(pm.JobRun.id))).all()
            for job_run in job_runs:
                await db.refresh(run)
                if run.status == "cancelled":
                    stage_run.status = "cancelled"
                    stage_run.finished_at = datetime.now(timezone.utc)
                    await db.commit()
                    return
                job_run.status = "running"
                job_run.started_at = datetime.now(timezone.utc)
                await db.commit()
                await publish_log(redis, str(run.id), "stdout", f"{job_run.name}: started")
                try:
                    await asyncio.sleep(0.1)
                    job_run.status = "success"
                    job_run.exit_code = 0
                    job_run.finished_at = datetime.now(timezone.utc)
                    await db.commit()
                    await publish_log(redis, str(run.id), "stdout", f"{job_run.name}: completed")
                except Exception:
                    await fail_run(db, run, stage_run, job_run)
                    await publish_log(redis, str(run.id), "stderr", f"{job_run.name}: failed")
                    return
            stage_run.status = "success"
            stage_run.finished_at = datetime.now(timezone.utc)
            await db.commit()

        await db.refresh(run)
        if run.status == "cancelled":
            return
        run.status = "success"
        run.finished_at = datetime.now(timezone.utc)
        await db.commit()


async def main() -> None:
    configure_logging()
    redis = get_redis()
    while True:
        message = await redis.blpop("queue:pipeline", timeout=1)
        if message is None:
            continue
        try:
            payload = json.loads(message[1])
            await process_run(payload)
        except Exception:
            continue


if __name__ == "__main__":
    asyncio.run(main())
