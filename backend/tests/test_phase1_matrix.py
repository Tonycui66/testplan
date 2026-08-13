import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.exceptions import NotFoundError
from app.dependencies import require_project_access
from app.modules.project import router as project_router
from app.modules.project.schemas import IterationUpdate
from app.modules.user import router as user_router
from app.modules.user.schemas import RefreshRequest


class FakeDB:
    def __init__(self, scalar_result=None, get_result=None):
        self.scalar = AsyncMock(return_value=scalar_result)
        self.get = AsyncMock(return_value=get_result)
        self.commit = AsyncMock()


class PrefixedString(str):
    def removeprefix(self, prefix):
        return self[len(prefix):] if self.startswith(prefix) else self


class FakeRedis:
    def __init__(self):
        self.data = {}

    async def set(self, key, value, ex=None):
        self.data[key] = value

    async def get(self, key):
        return self.data.get(key)

    async def delete(self, key):
        self.data.pop(key, None)


def test_project_permission_matrix() -> None:
    project_id = str(uuid4())
    user = SimpleNamespace(id=uuid4(), is_superadmin=False)

    async def run():
        request = SimpleNamespace(path_params={"project_id": project_id}, method="GET")
        db = FakeDB(scalar_result=None)
        with pytest.raises(HTTPException) as exc:
            await require_project_access(request, db, user)
        assert exc.value.status_code == 403

        viewer = SimpleNamespace(role="viewer")
        db = FakeDB(scalar_result=viewer)
        request.method = "PATCH"
        with pytest.raises(HTTPException) as exc:
            await require_project_access(request, db, user)
        assert exc.value.status_code == 403

        member = SimpleNamespace(role="member")
        db = FakeDB(scalar_result=member)
        request.method = "POST"
        await require_project_access(request, db, user)

        owner = SimpleNamespace(role="owner")
        db = FakeDB(scalar_result=owner)
        request.method = "DELETE"
        await require_project_access(request, db, user)

    asyncio.run(run())


def test_refresh_rotation_rejects_old_token(monkeypatch) -> None:
    user_id = uuid4()
    user = SimpleNamespace(id=user_id, is_active=True, deleted_at=None, email="user@example.com", name="User", avatar_url=None, is_superadmin=False)
    old_token = "old-token"
    redis = FakeRedis()
    redis.data["refresh:old-jti"] = str(user_id)
    monkeypatch.setattr(user_router, "get_redis", lambda: redis)
    monkeypatch.setattr(
        user_router,
        "decode_token",
        lambda token: {"sub": PrefixedString(f"refresh:{user_id}"), "type": "refresh", "jti": "old-jti"},
    )

    async def run():
        db = FakeDB(get_result=user)
        first = await user_router.refresh(RefreshRequest(refresh_token=old_token), db)
        assert first.access_token
        assert first.refresh_token != old_token
        assert "refresh:old-jti" not in redis.data

        db = FakeDB(get_result=user)
        with pytest.raises(HTTPException) as exc:
            await user_router.refresh(RefreshRequest(refresh_token=old_token), db)
        assert exc.value.status_code == 401

    asyncio.run(run())


def test_soft_deleted_iteration_patch_delete_return_404() -> None:
    project_id = uuid4()
    iteration_id = uuid4()
    user = SimpleNamespace(id=uuid4(), is_superadmin=False)

    async def run():
        db = FakeDB(scalar_result=None)
        with pytest.raises(NotFoundError):
            await project_router.update_iteration(
                project_id,
                iteration_id,
                IterationUpdate(name="still visible"),
                db,
                user,
            )

        db = FakeDB(scalar_result=None)
        with pytest.raises(NotFoundError):
            await project_router.delete_iteration(project_id, iteration_id, db, user)

    asyncio.run(run())
