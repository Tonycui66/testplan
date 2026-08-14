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
