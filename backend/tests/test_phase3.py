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

import pytest
from pydantic import ValidationError

from app.modules.artifact.schemas import ArtifactCreate
from app.modules.deploy.schemas import EnvironmentCreate
from app.modules.test.schemas import CaseCreate


def test_artifact_storage_constraints() -> None:
    with pytest.raises(ValidationError):
        ArtifactCreate(name="x", version="1", size_bytes=-1, storage_path="/tmp/../bad")
    with pytest.raises(ValidationError):
        ArtifactCreate(name="x", version="1", size_bytes=1, checksum="not-hex")


def test_deploy_and_test_enum_validation() -> None:
    with pytest.raises(ValidationError):
        EnvironmentCreate(name="env", type="invalid")
    with pytest.raises(ValidationError):
        CaseCreate(suite_id="00000000-0000-0000-0000-000000000000", title="x", steps="s", expected="e", priority="urgent")

from app.modules.deploy.schemas import K8sConfig, SshConfig


def test_artifact_name_and_version_reject_path_traversal() -> None:
    with pytest.raises(ValidationError):
        ArtifactCreate(name="../../etc", version="passwd", size_bytes=1)
    with pytest.raises(ValidationError):
        ArtifactCreate(name="app", version="../bad", size_bytes=1)


def test_deploy_config_requires_typed_credential_ref() -> None:
    ssh = SshConfig(host="example.com", username="deploy", credential_ref="cred-1")
    assert ssh.credential_ref == "cred-1"
    k8s = K8sConfig(cluster_ref="cluster-a", credential_ref="cred-2")
    assert k8s.namespace is None


def test_artifact_rejects_dot_segments() -> None:
    with pytest.raises(ValidationError):
        ArtifactCreate(name=".", version="x", size_bytes=1)
    with pytest.raises(ValidationError):
        ArtifactCreate(name="..", version="x", size_bytes=1)
    with pytest.raises(ValidationError):
        ArtifactCreate(name="app", version="..", size_bytes=1)


def test_phase3_execution_routes_exist() -> None:
    paths = {route.path for route in app.routes}
    for path in [
        "/api/v1/projects/{project_id}/tests/runs",
        "/api/v1/projects/{project_id}/deploy/tasks",
        "/api/v1/projects/{project_id}/artifacts/repositories/{repository_id}/artifacts",
    ]:
        assert path in paths
