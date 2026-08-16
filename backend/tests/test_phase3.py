from app.main import app
from app.modules.artifact.schemas import ArtifactCreate, RepositoryCreate
from app.modules.deploy.schemas import EnvironmentCreate
from app.modules.test.schemas import CaseCreate, SuiteCreate


def test_phase3_schemas_accept_core_payloads() -> None:
    assert RepositoryCreate(name="npm").name == "npm"
    assert ArtifactCreate(name="app", version="1.0.0", size_bytes=10, storage_path="/tmp/app").version == "1.0.0"
    assert SuiteCreate(name="suite").name == "suite"
    assert CaseCreate(suite_id="00000000-0000-0000-0000-000000000000", title="case", steps="step", expected="ok").title == "case"
    assert EnvironmentCreate(name="prod").name == "prod"


def test_phase3_routes_exist() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/projects/{project_id}/tests/suites" in paths
    assert "/api/v1/projects/{project_id}/deploy/environments" in paths
    assert "/api/v1/projects/{project_id}/artifacts/repositories" in paths
