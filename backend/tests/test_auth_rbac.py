from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.security import create_token
from app.dependencies import get_current_user
from app.main import app
from app.modules.user import router as user_router
from types import SimpleNamespace


class FakeRedis:
    def __init__(self):
        self.data = {}

    async def set(self, key, value, ex=None):
        self.data[key] = value

    async def get(self, key):
        return self.data.get(key)

    async def delete(self, key):
        self.data.pop(key, None)


def normal_user() -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), email="user@example.com", is_active=True, is_superadmin=False)


def test_logout_revokes_refresh_token(monkeypatch) -> None:
    app.dependency_overrides[get_current_user] = normal_user
    redis = FakeRedis()
    redis.data["refresh:revoke-me"] = "user"
    monkeypatch.setattr(user_router, "get_redis", lambda: redis)
    refresh_token = create_token(f"refresh:{uuid4()}", timedelta(days=7), token_type="refresh", jti="revoke-me")

    client = TestClient(app)
    response = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert response.status_code == 204
    assert "refresh:revoke-me" not in redis.data
    app.dependency_overrides.clear()


def test_admin_users_requires_superadmin() -> None:
    app.dependency_overrides[get_current_user] = normal_user
    client = TestClient(app)
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 403
    app.dependency_overrides.clear()
