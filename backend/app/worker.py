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


async def process_run(payload: Dict[str, Any]) -> None:
    session_factory = async_sessionmaker(get_database_engine(), expire_on_commit=False)
    redis = get_redis()
    async with session_factory() as db:
        run = await db.get(pm.PipelineRun, UUID(payload["run_id"]))
        if run is None:
            return
        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        await db.commit()
        for job_run_id in payload["job_run_ids"].values():
            job_run = await db.get(pm.JobRun, UUID(job_run_id))
            if job_run is None:
                continue
            job_run.status = "running"
            job_run.started_at = datetime.now(timezone.utc)
            await db.commit()
            await publish_log(redis, str(run.id), "stdout", f"{job_run.name}: started")
            await asyncio.sleep(0.1)
            job_run.status = "success"
            job_run.exit_code = 0
            job_run.finished_at = datetime.now(timezone.utc)
            await publish_log(redis, str(run.id), "stdout", f"{job_run.name}: completed")
            await db.commit()
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
