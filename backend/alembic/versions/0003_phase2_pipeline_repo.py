"""phase 2 pipeline and repo tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-15
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

upgrade_statements = [
    """CREATE TABLE pipeline.pipelines (
        id UUID PRIMARY KEY,
        project_id UUID NOT NULL,
        name VARCHAR(200) NOT NULL,
        description TEXT,
        is_enabled BOOLEAN NOT NULL DEFAULT true,
        run_counter INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE pipeline.pipeline_stages (
        id UUID PRIMARY KEY,
        pipeline_id UUID NOT NULL,
        name VARCHAR(100) NOT NULL,
        "order" INTEGER NOT NULL DEFAULT 0,
        condition VARCHAR(20) NOT NULL DEFAULT 'always',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE INDEX idx_stage_pipeline ON pipeline.pipeline_stages (pipeline_id, "order")""",
    """CREATE TABLE pipeline.pipeline_jobs (
        id UUID PRIMARY KEY,
        stage_id UUID NOT NULL,
        name VARCHAR(200) NOT NULL,
        image VARCHAR(500) NOT NULL,
        script TEXT NOT NULL,
        timeout_seconds INTEGER NOT NULL DEFAULT 3600,
        "order" INTEGER NOT NULL DEFAULT 0,
        variables JSONB NOT NULL DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE pipeline.pipeline_triggers (
        id UUID PRIMARY KEY,
        pipeline_id UUID NOT NULL,
        type VARCHAR(20) NOT NULL DEFAULT 'manual',
        config JSONB NOT NULL DEFAULT '{}',
        is_enabled BOOLEAN NOT NULL DEFAULT true
    )""",
    """CREATE TABLE pipeline.pipeline_runs (
        id UUID PRIMARY KEY,
        pipeline_id UUID NOT NULL,
        run_number INTEGER NOT NULL,
        trigger_type VARCHAR(20) NOT NULL,
        trigger_user_id UUID,
        branch VARCHAR(255),
        commit_sha VARCHAR(40),
        variables JSONB NOT NULL DEFAULT '{}',
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        started_at TIMESTAMPTZ,
        finished_at TIMESTAMPTZ
    )""",
    """CREATE INDEX idx_run_pipeline ON pipeline.pipeline_runs (pipeline_id, run_number DESC)""",
    """CREATE TABLE pipeline.stage_runs (
        id UUID PRIMARY KEY,
        run_id UUID NOT NULL,
        stage_id UUID NOT NULL,
        name VARCHAR(100) NOT NULL,
        status VARCHAR(20) NOT NULL,
        "order" INTEGER NOT NULL,
        started_at TIMESTAMPTZ,
        finished_at TIMESTAMPTZ
    )""",
    """CREATE TABLE pipeline.job_runs (
        id UUID PRIMARY KEY,
        stage_run_id UUID NOT NULL,
        job_id UUID NOT NULL,
        name VARCHAR(200) NOT NULL,
        status VARCHAR(20) NOT NULL,
        exit_code INTEGER,
        started_at TIMESTAMPTZ,
        finished_at TIMESTAMPTZ
    )""",
    """CREATE TABLE pipeline.job_logs (
        id UUID PRIMARY KEY,
        job_run_id UUID NOT NULL,
        line_number INTEGER NOT NULL,
        content TEXT NOT NULL,
        stream VARCHAR(6) NOT NULL,
        timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE INDEX idx_log_job ON pipeline.job_logs (job_run_id, line_number)""",
    """CREATE TABLE repo.repo_connections (
        id UUID PRIMARY KEY,
        project_id UUID NOT NULL,
        provider VARCHAR(20) NOT NULL,
        repo_url VARCHAR(500) NOT NULL,
        repo_name VARCHAR(200) NOT NULL,
        oauth_token_id UUID,
        webhook_secret VARCHAR(255),
        is_active BOOLEAN NOT NULL DEFAULT true,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE repo.webhook_events (
        id UUID PRIMARY KEY,
        connection_id UUID NOT NULL,
        event_type VARCHAR(50) NOT NULL,
        payload JSONB NOT NULL,
        processed BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""",
    """CREATE TABLE repo.branches (
        id UUID PRIMARY KEY,
        connection_id UUID NOT NULL,
        name VARCHAR(255) NOT NULL,
        last_commit_sha VARCHAR(40),
        last_commit_message TEXT,
        last_commit_author VARCHAR(255),
        last_commit_date TIMESTAMPTZ
    )""",
    """CREATE TABLE repo.commits (
        id UUID PRIMARY KEY,
        connection_id UUID NOT NULL,
        branch VARCHAR(255) NOT NULL,
        sha VARCHAR(40) NOT NULL,
        message TEXT NOT NULL,
        author_name VARCHAR(255) NOT NULL,
        author_email VARCHAR(255) NOT NULL,
        committed_at TIMESTAMPTZ NOT NULL
    )""",
]


def upgrade() -> None:
    for statement in upgrade_statements:
        op.execute(statement)


def downgrade() -> None:
    tables = [
        "repo.commits",
        "repo.branches",
        "repo.webhook_events",
        "repo.repo_connections",
        "pipeline.job_logs",
        "pipeline.job_runs",
        "pipeline.stage_runs",
        "pipeline.pipeline_runs",
        "pipeline.pipeline_triggers",
        "pipeline.pipeline_jobs",
        "pipeline.pipeline_stages",
        "pipeline.pipelines",
    ]
    for table in tables:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
