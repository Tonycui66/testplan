from app.modules.pipeline.schemas import JobInput, PipelineCreate, StageInput
from app.modules.repo.schemas import RepoConnectionCreate


def test_pipeline_schema_accepts_nested_stages_and_jobs() -> None:
    payload = PipelineCreate(
        name="Build and test",
        stages=[
            StageInput(
                name="Build",
                order=0,
                condition="always",
                jobs=[JobInput(name="echo", image="alpine:3.18", script="echo ok", order=0)],
            )
        ],
    )
    assert payload.stages[0].jobs[0].image == "alpine:3.18"


def test_repo_connection_requires_provider_and_url() -> None:
    payload = RepoConnectionCreate(
        provider="github",
        repo_url="https://github.com/example/repo",
        repo_name="example/repo",
    )
    assert payload.repo_name == "example/repo"

from datetime import datetime
from uuid import uuid4

from app.modules.repo.schemas import RepoConnectionResponse


def test_repo_connection_response_does_not_expose_webhook_secret() -> None:
    response = RepoConnectionResponse(
        id=uuid4(),
        project_id=uuid4(),
        provider="github",
        repo_url="https://github.com/example/repo",
        repo_name="example/repo",
        is_active=True,
        created_at=datetime(2026, 8, 15),
    )
    assert "webhook_secret" not in response.model_dump()

from app.modules.pipeline.schemas import PipelineUpdate


def test_pipeline_update_accepts_stages() -> None:
    payload = PipelineUpdate(stages=[StageInput(name="Cleanup", condition="on_failure", jobs=[])])
    assert payload.stages[0].condition == "on_failure"

from app.main import app


def test_phase2_websocket_contract_path_exists() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v1/ws/pipelines/{pipeline_id}/runs/{run_id}/logs" in paths
