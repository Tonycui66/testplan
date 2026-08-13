from unittest.mock import AsyncMock, MagicMock

from app import main


def test_health_ok(client, monkeypatch) -> None:
    engine = MagicMock()
    connection = AsyncMock()
    engine.connect.return_value.__aenter__.return_value = connection
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)

    monkeypatch.setattr(main, "get_database_engine", lambda: engine)
    monkeypatch.setattr(main, "get_redis", lambda: redis)

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["checks"]["database"] == "ok"
    assert response.json()["checks"]["redis"] == "ok"


def test_health_degraded_when_database_fails(client, monkeypatch) -> None:
    engine = MagicMock()
    connection = AsyncMock()
    connection.execute.side_effect = RuntimeError("database unavailable")
    engine.connect.return_value.__aenter__.return_value = connection
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)

    monkeypatch.setattr(main, "get_database_engine", lambda: engine)
    monkeypatch.setattr(main, "get_redis", lambda: redis)

    response = client.get("/api/v1/health")
    assert response.status_code == 503
    assert response.json()["checks"]["database"] == "down"
    assert response.json()["checks"]["redis"] == "ok"
