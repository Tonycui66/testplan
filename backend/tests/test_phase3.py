import hashlib
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.dependencies import get_current_user, get_db, require_project_access
from app.main import app
from app.modules.artifact import models as am
from app.modules.artifact.schemas import ArtifactCreate, RepositoryCreate
from app.modules.artifact.storage import LocalArtifactStorage, get_artifact_storage
from app.modules.deploy.schemas import EnvironmentCreate, K8sConfig, SshConfig
from app.modules.test.schemas import CaseCreate, CaseUpdate, SuiteCreate


def test_phase3_schemas_accept_core_payloads() -> None:
    assert RepositoryCreate(name="npm").name == "npm"
    assert ArtifactCreate(name="app", version="1.0.0").version == "1.0.0"
    assert SuiteCreate(name="suite").name == "suite"
    assert CaseCreate(suite_id="00000000-0000-0000-0000-000000000000", title="case", steps="step", expected="ok").title == "case"
    assert EnvironmentCreate(name="prod").name == "prod"


def test_phase3_routes_exist() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/projects/{project_id}/tests/suites" in paths
    assert "/api/v1/projects/{project_id}/deploy/environments" in paths
    assert "/api/v1/projects/{project_id}/artifacts/repositories" in paths


def test_artifact_name_and_version_reject_path_traversal() -> None:
    with pytest.raises(ValidationError):
        ArtifactCreate(name="../../etc", version="passwd")
    with pytest.raises(ValidationError):
        ArtifactCreate(name="app", version="../bad")


def test_artifact_rejects_dot_segments() -> None:
    with pytest.raises(ValidationError):
        ArtifactCreate(name=".", version="x")
    with pytest.raises(ValidationError):
        ArtifactCreate(name="..", version="x")
    with pytest.raises(ValidationError):
        ArtifactCreate(name="app", version="..")


def test_deploy_and_test_enum_validation() -> None:
    with pytest.raises(ValidationError):
        EnvironmentCreate(name="env", type="invalid")
    with pytest.raises(ValidationError):
        CaseCreate(suite_id="00000000-0000-0000-0000-000000000000", title="x", steps="s", expected="e", priority="urgent")


def test_deploy_config_requires_typed_credential_ref() -> None:
    ssh = SshConfig(host="example.com", username="deploy", credential_ref="cred-1")
    assert ssh.credential_ref == "cred-1"
    k8s = K8sConfig(cluster_ref="cluster-a", credential_ref="cred-2")
    assert k8s.namespace is None


def test_phase3_execution_routes_exist() -> None:
    paths = {route.path for route in app.routes}
    for path in [
        "/api/v1/projects/{project_id}/tests/runs",
        "/api/v1/projects/{project_id}/deploy/tasks",
        "/api/v1/projects/{project_id}/artifacts/repositories/{repository_id}/artifacts",
    ]:
        assert path in paths


def test_case_update_rejects_null_steps_or_expected() -> None:
    with pytest.raises(ValidationError):
        CaseUpdate(steps="", expected="")


def test_case_update_explicit_none_is_dropped() -> None:
    payload = CaseUpdate(steps=None, expected=None)
    assert "steps" not in payload.model_dump(exclude_unset=True, exclude_none=True)
    assert "expected" not in payload.model_dump(exclude_unset=True, exclude_none=True)


class FakeArtifactDB:
    def __init__(self, repo=None, artifact=None, scalar_result=None):
        self.repo = repo
        self.artifact = artifact
        self.scalar_result = scalar_result
        self.added = []

    async def get(self, model, ident):
        if model is am.ArtifactRepository:
            return self.repo
        if model is am.Artifact:
            return self.artifact
        return None

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        return None

    async def refresh(self, obj):
        return None

    async def scalar(self, stmt):
        return self.scalar_result


def _install_artifact_dependencies(db, user, storage) -> None:
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_project_access] = lambda: None
    app.dependency_overrides[get_artifact_storage] = lambda: storage


def _clear_artifact_dependencies() -> None:
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(require_project_access, None)
    app.dependency_overrides.pop(get_artifact_storage, None)


def test_artifact_upload_rejects_unsupported_content_type(client, tmp_path) -> None:
    project_id = uuid4()
    repository_id = uuid4()
    storage = LocalArtifactStorage(str(tmp_path / "artifacts"), allowed_content_types={"application/gzip"})
    repo = am.ArtifactRepository(project_id=project_id, name="release", type="generic")
    db = FakeArtifactDB(repo=repo, scalar_result=SimpleNamespace(role="owner"))
    _install_artifact_dependencies(db, SimpleNamespace(id=uuid4(), is_superadmin=False), storage)
    try:
        response = client.post(
            f"/api/v1/projects/{project_id}/artifacts/repositories/{repository_id}/artifacts",
            data={"name": "app", "version": "1.0.0", "metadata": "{}"},
            files={"file": ("app.txt", b"hello", "text/html")},
        )
    finally:
        _clear_artifact_dependencies()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_artifact_upload_enforces_max_size(client, tmp_path) -> None:
    project_id = uuid4()
    repository_id = uuid4()
    storage = LocalArtifactStorage(str(tmp_path / "artifacts"), max_size_bytes=4, allowed_content_types={"application/gzip"})
    repo = am.ArtifactRepository(project_id=project_id, name="release", type="generic")
    db = FakeArtifactDB(repo=repo, scalar_result=SimpleNamespace(role="owner"))
    _install_artifact_dependencies(db, SimpleNamespace(id=uuid4(), is_superadmin=False), storage)
    try:
        response = client.post(
            f"/api/v1/projects/{project_id}/artifacts/repositories/{repository_id}/artifacts",
            data={"name": "app", "version": "1.0.0", "metadata": "{}"},
            files={"file": ("app.tar.gz", b"12345", "application/gzip")},
        )
    finally:
        _clear_artifact_dependencies()

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_artifact_upload_requires_project_owner(client, tmp_path) -> None:
    project_id = uuid4()
    repository_id = uuid4()
    storage = LocalArtifactStorage(str(tmp_path / "artifacts"))
    repo = am.ArtifactRepository(project_id=project_id, name="release", type="generic")
    db = FakeArtifactDB(repo=repo, scalar_result=SimpleNamespace(role="member"))
    _install_artifact_dependencies(db, SimpleNamespace(id=uuid4(), is_superadmin=False), storage)
    try:
        response = client.post(
            f"/api/v1/projects/{project_id}/artifacts/repositories/{repository_id}/artifacts",
            data={"name": "app", "version": "1.0.0", "metadata": "{}"},
            files={"file": ("app.tar.gz", b"hello", "application/gzip")},
        )
    finally:
        _clear_artifact_dependencies()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_artifact_upload_writes_file_and_computes_checksum(client, tmp_path) -> None:
    project_id = uuid4()
    repository_id = uuid4()
    payload_bytes = b"artifact-bytes"
    storage = LocalArtifactStorage(str(tmp_path / "artifacts"))
    repo = am.ArtifactRepository(project_id=project_id, name="release", type="generic")
    db = FakeArtifactDB(repo=repo, scalar_result=SimpleNamespace(role="owner"))
    user = SimpleNamespace(id=uuid4(), is_superadmin=False)
    _install_artifact_dependencies(db, user, storage)
    try:
        response = client.post(
            f"/api/v1/projects/{project_id}/artifacts/repositories/{repository_id}/artifacts",
            data={"name": "app", "version": "1.0.0", "metadata": '{"ci":true}'},
            files={"file": ("app.tar.gz", payload_bytes, "application/gzip")},
        )
    finally:
        _clear_artifact_dependencies()

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "app"
    assert data["version"] == "1.0.0"
    assert data["size_bytes"] == len(payload_bytes)
    assert data["checksum"] == hashlib.sha256(payload_bytes).hexdigest()
    assert data["content_type"] == "application/gzip"
    assert "storage_path" not in data
    assert len(db.added) == 1
    stored_path = db.added[0].storage_path
    stored_file = tmp_path / "artifacts" / stored_path
    assert stored_file.read_bytes() == payload_bytes
    assert db.added[0].artifact_metadata == {"ci": True}


def test_artifact_download_streams_stored_file(client, tmp_path) -> None:
    project_id = uuid4()
    repository_id = uuid4()
    artifact_id = uuid4()
    root = tmp_path / "artifacts"
    relative_path = Path(str(project_id)) / str(repository_id) / "abc-app.tar.gz"
    stored_file = root / relative_path
    stored_file.parent.mkdir(parents=True)
    stored_file.write_bytes(b"download-bytes")

    storage = LocalArtifactStorage(str(root))
    repo = am.ArtifactRepository(project_id=project_id, name="release", type="generic")
    artifact = am.Artifact(
        id=artifact_id,
        repository_id=repository_id,
        name="app",
        version="1.0.0",
        size_bytes=len(b"download-bytes"),
        storage_path=str(relative_path),
        checksum=hashlib.sha256(b"download-bytes").hexdigest(),
        artifact_metadata={},
    )
    db = FakeArtifactDB(repo=repo, artifact=artifact)
    _install_artifact_dependencies(db, SimpleNamespace(id=uuid4(), is_superadmin=False), storage)
    try:
        response = client.get(
            f"/api/v1/projects/{project_id}/artifacts/repositories/{repository_id}/artifacts/{artifact_id}/download"
        )
    finally:
        _clear_artifact_dependencies()

    assert response.status_code == 200
    assert response.content == b"download-bytes"
    assert "attachment" in response.headers.get("content-disposition", "")
    assert response.headers["content-type"] != "application/json"


def test_artifact_download_rejects_cross_project_repository(client, tmp_path) -> None:
    project_id = uuid4()
    repository_id = uuid4()
    artifact_id = uuid4()
    storage = LocalArtifactStorage(str(tmp_path / "artifacts"))
    repo = am.ArtifactRepository(project_id=uuid4(), name="other", type="generic")
    db = FakeArtifactDB(repo=repo)
    _install_artifact_dependencies(db, SimpleNamespace(id=uuid4(), is_superadmin=False), storage)
    try:
        response = client.get(
            f"/api/v1/projects/{project_id}/artifacts/repositories/{repository_id}/artifacts/{artifact_id}/download"
        )
    finally:
        _clear_artifact_dependencies()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
