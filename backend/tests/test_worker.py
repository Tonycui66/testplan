import asyncio
import json
from collections import deque
from unittest.mock import AsyncMock
from uuid import uuid4

from app import worker


class FakeRedis:
    def __init__(self, messages):
        self.messages = deque(messages)
        self.calls = []

    async def blpop(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if not self.messages:
            return None
        return self.messages.popleft()


def test_worker_consumes_pipeline_and_deploy_queues(monkeypatch) -> None:
    run_id = uuid4()
    task_id = uuid4()
    redis = FakeRedis(
        [
            ("queue:pipeline", json.dumps({"run_id": str(run_id)})),
            ("queue:deploy", json.dumps({"task_id": str(task_id)})),
        ]
    )
    process_run = AsyncMock()
    process_deploy_task = AsyncMock()
    monkeypatch.setattr(worker, "process_run", process_run)
    monkeypatch.setattr(worker, "process_deploy_task", process_deploy_task)

    async def run():
        assert await worker.consume_once(redis) is True
        assert await worker.consume_once(redis) is True

    asyncio.run(run())

    assert redis.calls == [
        ((("queue:pipeline", "queue:deploy"),), {"timeout": 1}),
        ((("queue:pipeline", "queue:deploy"),), {"timeout": 1}),
    ]
    process_run.assert_awaited_once_with({"run_id": str(run_id)})
    process_deploy_task.assert_awaited_once_with(str(task_id))
