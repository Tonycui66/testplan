"""phase 3 test deploy artifact tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-15
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

upgrade_statements = [
    """CREATE TABLE artifact.repositories (
        id UUID PRIMARY KEY,
        project_id UUID NOT NULL,
        name VARCHAR(200) NOT NULL,
        type VARCHAR(20) NOT NULL DEFAULT 'generic',
        description TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE artifact.artifacts (
        id UUID PRIMARY KEY,
        repository_id UUID NOT NULL,
        name VARCHAR(255) NOT NULL,
        version VARCHAR(100) NOT NULL,
        size_bytes BIGINT NOT NULL,
        storage_path VARCHAR(500) NOT NULL,
        checksum VARCHAR(64),
        metadata JSONB NOT NULL DEFAULT '{}'
    )""",
    """CREATE TABLE artifact.docker_images (
        id UUID PRIMARY KEY,
        repository_id UUID NOT NULL,
        image_name VARCHAR(255) NOT NULL,
        tag VARCHAR(100) NOT NULL,
        digest VARCHAR(71),
        size_bytes BIGINT,
        pushed_by UUID NOT NULL
    )""",
    """CREATE TABLE artifact.artifact_versions (
        id UUID PRIMARY KEY,
        repository_id UUID NOT NULL,
        version VARCHAR(100) NOT NULL,
        release_notes TEXT,
        pipeline_run_id UUID
    )""",
    """CREATE UNIQUE INDEX uq_av_repo_version ON artifact.artifact_versions (repository_id, version)""",
    """CREATE TABLE test.test_suites (
        id UUID PRIMARY KEY,
        project_id UUID NOT NULL,
        name VARCHAR(200) NOT NULL,
        description TEXT,
        parent_id UUID,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE test.test_cases (
        id UUID PRIMARY KEY,
        suite_id UUID NOT NULL,
        title VARCHAR(500) NOT NULL,
        steps TEXT NOT NULL,
        expected TEXT NOT NULL,
        priority VARCHAR(10) NOT NULL DEFAULT 'medium',
        type VARCHAR(20) NOT NULL DEFAULT 'manual',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE test.test_plans (
        id UUID PRIMARY KEY,
        project_id UUID NOT NULL,
        iteration_id UUID,
        name VARCHAR(200) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'draft',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE test.test_plan_cases (
        id UUID PRIMARY KEY,
        plan_id UUID NOT NULL,
        case_id UUID NOT NULL,
        "order" INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE UNIQUE INDEX uq_plan_case ON test.test_plan_cases (plan_id, case_id)""",
    """CREATE TABLE test.test_runs (
        id UUID PRIMARY KEY,
        plan_id UUID NOT NULL,
        environment_id UUID,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        started_by UUID NOT NULL,
        started_at TIMESTAMPTZ,
        finished_at TIMESTAMPTZ
    )""",
    """CREATE TABLE test.test_run_results (
        id UUID PRIMARY KEY,
        run_id UUID NOT NULL,
        case_id UUID NOT NULL,
        status VARCHAR(10) NOT NULL DEFAULT 'pending',
        comment TEXT,
        executed_by UUID,
        executed_at TIMESTAMPTZ
    )""",
    """CREATE UNIQUE INDEX uq_run_case ON test.test_run_results (run_id, case_id)""",
    """CREATE TABLE deploy.environments (
        id UUID PRIMARY KEY,
        project_id UUID NOT NULL,
        name VARCHAR(100) NOT NULL,
        type VARCHAR(20) NOT NULL DEFAULT 'ssh',
        config JSONB NOT NULL DEFAULT '{}',
        is_protected BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE deploy.deploy_tasks (
        id UUID PRIMARY KEY,
        environment_id UUID NOT NULL,
        artifact_id UUID,
        branch VARCHAR(255),
        commit_sha VARCHAR(40),
        strategy VARCHAR(20) NOT NULL DEFAULT 'rolling',
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        trigger_user_id UUID NOT NULL,
        started_at TIMESTAMPTZ,
        finished_at TIMESTAMPTZ
    )""",
    """CREATE TABLE deploy.deploy_records (
        id UUID PRIMARY KEY,
        task_id UUID NOT NULL,
        environment_id UUID NOT NULL,
        status VARCHAR(20) NOT NULL,
        log TEXT,
        deployed_by UUID NOT NULL,
        deployed_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE deploy.ssh_credentials (
        id UUID PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        host VARCHAR(255) NOT NULL,
        port INTEGER NOT NULL DEFAULT 22,
        username VARCHAR(100) NOT NULL,
        private_key_encrypted TEXT NOT NULL
    )""",
    """CREATE TABLE deploy.k8s_clusters (
        id UUID PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        kubeconfig_encrypted TEXT NOT NULL
    )""",
]


def upgrade() -> None:
    for statement in upgrade_statements:
        op.execute(statement)


def downgrade() -> None:
    tables = [
        "deploy.k8s_clusters",
        "deploy.ssh_credentials",
        "deploy.deploy_records",
        "deploy.deploy_tasks",
        "deploy.environments",
        "test.test_run_results",
        "test.test_runs",
        "test.test_plan_cases",
        "test.test_plans",
        "test.test_cases",
        "test.test_suites",
        "artifact.artifact_versions",
        "artifact.docker_images",
        "artifact.artifacts",
        "artifact.repositories",
    ]
    for table in tables:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
