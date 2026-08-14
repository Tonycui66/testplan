import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.exceptions import ConflictError, NotFoundError
from app.dependencies import require_project_access
from app.modules.project import router as project_router
from app.modules.project.schemas import BoardCardCreate, BoardCardUpdate, BoardColumnUpdate, BugCreate, BugUpdate, IterationUpdate
from app.modules.user import router as user_router
from app.modules.user.schemas import RefreshRequest, TeamUpdate
from pydantic import ValidationError


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


def test_board_column_rejects_resource_from_other_project() -> None:
    project_a = uuid4()
    project_b = uuid4()
    column_id = uuid4()
    board_a = SimpleNamespace(id=uuid4(), project_id=project_a)
    board_b = SimpleNamespace(id=uuid4(), project_id=project_b)
    user = SimpleNamespace(id=uuid4(), is_superadmin=False)

    async def run():
        db = FakeDB()
        db.scalar.side_effect = [board_b, None]
        with pytest.raises(NotFoundError):
            await project_router.update_board_column(
                project_a,
                column_id,
                BoardColumnUpdate(name="bad"),
                db,
                user,
            )

        db = FakeDB()
        db.scalar.side_effect = [board_b, None]
        with pytest.raises(NotFoundError):
            await project_router.delete_board_column(project_a, column_id, db, user)

    asyncio.run(run())


def test_board_card_rejects_resource_from_other_project() -> None:
    project_a = uuid4()
    project_b = uuid4()
    card_id = uuid4()
    board_b = SimpleNamespace(id=uuid4(), project_id=project_b)
    user = SimpleNamespace(id=uuid4(), is_superadmin=False)

    async def run():
        db = FakeDB()
        db.scalar.side_effect = [board_b, None]
        with pytest.raises(NotFoundError):
            await project_router.update_board_card(
                project_a,
                card_id,
                BoardCardUpdate(order=1),
                db,
                user,
            )

        db = FakeDB()
        db.scalar.side_effect = [board_b, None]
        with pytest.raises(NotFoundError):
            await project_router.delete_board_card(project_a, card_id, db, user)

    asyncio.run(run())


def test_team_pagination_is_normalized() -> None:
    user = SimpleNamespace(id=uuid4(), is_superadmin=False)

    async def run():
        db = FakeDB()
        db.scalar = AsyncMock(return_value=0)
        db.scalars = AsyncMock(return_value=SimpleNamespace(all=lambda: []))
        result = await user_router.list_teams(1, 200, db, user)
        assert result["meta"]["page_size"] == 100

    asyncio.run(run())


def test_bug_enum_accepts_blocker_and_reopened() -> None:
    assert BugCreate(title="Bug", severity="blocker").severity == "blocker"
    assert BugUpdate(status="reopened").status == "reopened"
    with pytest.raises(ValidationError):
        BugCreate(title="Bug", severity="invalid")


def test_board_column_delete_rejects_nonempty_column() -> None:
    board = SimpleNamespace(id=uuid4())
    user = SimpleNamespace(id=uuid4(), is_superadmin=False)

    async def run():
        db = FakeDB()
        db.scalar.side_effect = [board, SimpleNamespace(id=uuid4()), 1]
        with pytest.raises(ConflictError):
            await project_router.delete_board_column(uuid4(), uuid4(), db, user)

    asyncio.run(run())


def test_board_card_rejects_column_from_other_board() -> None:
    board = SimpleNamespace(id=uuid4())
    user = SimpleNamespace(id=uuid4(), is_superadmin=False)

    async def run():
        db = FakeDB()
        db.scalar.side_effect = [board, None]
        with pytest.raises(NotFoundError):
            await project_router.create_board_card(
                uuid4(),
                BoardCardCreate(column_id=uuid4(), item_type="task", item_id=uuid4()),
                db,
                user,
            )

        card = SimpleNamespace(id=uuid4(), column_id=uuid4())
        db = FakeDB()
        db.scalar.side_effect = [board, card, None]
        with pytest.raises(NotFoundError):
            await project_router.update_board_card(
                uuid4(),
                card.id,
                BoardCardUpdate(column_id=uuid4()),
                db,
                user,
            )

    asyncio.run(run())


def test_project_detail_returns_stats() -> None:
    project = SimpleNamespace(
        id=uuid4(),
        name="Project",
        key="KEY",
        description=None,
        is_archived=False,
        created_at="2026-08-15T00:00:00Z",
        deleted_at=None,
    )
    user = SimpleNamespace(id=uuid4(), is_superadmin=False)

    async def run():
        db = FakeDB(get_result=project)
        db.scalar.side_effect = [1, 2, 3, 4, 5]
        result = await project_router.get_project(project.id, db, user)
        assert result["stats"] == {"iterations": 1, "requirements": 2, "tasks": 3, "bugs": 4, "members": 5}

    asyncio.run(run())


def test_team_role_permissions() -> None:
    team_id = uuid4()
    owner = SimpleNamespace(id=uuid4(), is_superadmin=False)
    member = SimpleNamespace(id=uuid4(), is_superadmin=False)

    async def run():
        team = SimpleNamespace(id=team_id, created_by=uuid4())
        db = FakeDB(get_result=team, scalar_result=SimpleNamespace(role="member"))
        with pytest.raises(HTTPException):
            await user_router.update_team(team_id, TeamUpdate(name="new"), db, member)

        db = FakeDB(get_result=team, scalar_result=SimpleNamespace(role="owner"))
        result = await user_router.get_team_with_role(team_id, owner, db, {"owner"})
        assert result.id == team_id

    asyncio.run(run())


def test_list_routes_accept_filters() -> None:
    project_id = uuid4()
    user = SimpleNamespace(id=uuid4(), is_superadmin=False)

    async def run():
        db = FakeDB()
        db.scalar = AsyncMock(return_value=0)
        db.scalars = AsyncMock(return_value=SimpleNamespace(all=lambda: []))
        await project_router.list_requirements(project_id, 1, 20, status="draft", priority="high", db=db, _=user)
        await project_router.list_tasks(project_id, 1, 20, status="todo", requirement_id=uuid4(), db=db, _=user)
        await project_router.list_bugs(project_id, 1, 20, severity="blocker", db=db, _=user)

    asyncio.run(run())
