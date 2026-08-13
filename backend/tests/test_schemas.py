from app.modules.project.schemas import RequirementUpdate
from app.modules.user.schemas import LogoutRequest, RegisterRequest


def test_register_request_requires_valid_email() -> None:
    payload = RegisterRequest(email="user@example.com", password="password123", name="User")
    assert payload.email == "user@example.com"


def test_logout_request_can_carry_refresh_token() -> None:
    payload = LogoutRequest(refresh_token="refresh-token")
    assert payload.refresh_token == "refresh-token"


def test_requirement_update_supports_partial_payload() -> None:
    payload = RequirementUpdate(status="done")
    assert payload.status == "done"
    assert payload.title is None
