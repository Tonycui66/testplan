from datetime import timedelta

from app.config import Settings
from app.core.security import create_token, decode_token


def test_access_token_default_ttl_matches_plan() -> None:
    settings = Settings()
    assert settings.access_token_expire_minutes == 1440


def test_access_and_refresh_tokens_have_types_and_jti() -> None:
    access = create_token("user-1", timedelta(minutes=30), token_type="access")
    refresh = create_token("refresh:user-1", timedelta(days=7), token_type="refresh", jti="jti-1")
    access_payload = decode_token(access)
    refresh_payload = decode_token(refresh)
    assert access_payload is not None and access_payload["type"] == "access"
    assert access_payload["jti"]
    assert refresh_payload is not None and refresh_payload["type"] == "refresh"
    assert refresh_payload["jti"] == "jti-1"


def test_refresh_token_subject_is_prefixed() -> None:
    token = create_token("refresh:user-1", token_type="refresh")
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"].startswith("refresh:")
