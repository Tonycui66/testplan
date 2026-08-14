"""phase 1 iam and project tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-13
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE iam.users (
        id UUID PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        name VARCHAR(100) NOT NULL,
        avatar_url VARCHAR(500),
        is_active BOOLEAN NOT NULL DEFAULT true,
        is_superadmin BOOLEAN NOT NULL DEFAULT false,
        last_login_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        deleted_at TIMESTAMPTZ
    )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX idx_users_email ON iam.users(email) WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE TABLE iam.roles (
        id UUID PRIMARY KEY,
        name VARCHAR(50) NOT NULL UNIQUE,
        description VARCHAR(255),
        is_system BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
        """
    )
    op.execute(
        """
        CREATE TABLE iam.user_roles (
        id UUID PRIMARY KEY,
        user_id UUID NOT NULL,
        role_id UUID NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_user_roles UNIQUE (user_id, role_id)
    )
        """
    )
    op.execute(
        """
        CREATE TABLE iam.teams (
        id UUID PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        created_by UUID NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
        """
    )
    op.execute(
        """
        CREATE TABLE iam.team_members (
        id UUID PRIMARY KEY,
        team_id UUID NOT NULL,
        user_id UUID NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'member',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_team_member UNIQUE (team_id, user_id)
    )
        """
    )
    op.execute(
        """
        CREATE TABLE iam.user_oauth_tokens (
        id UUID PRIMARY KEY,
        user_id UUID NOT NULL,
        provider VARCHAR(20) NOT NULL,
        access_token TEXT NOT NULL,
        refresh_token TEXT,
        expires_at TIMESTAMPTZ,
        provider_user_id VARCHAR(255)
    )
        """
    )
    op.execute(
        """
        CREATE TABLE project.projects (
        id UUID PRIMARY KEY,
        name VARCHAR(200) NOT NULL,
        key VARCHAR(10) NOT NULL,
        description TEXT,
        is_archived BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        deleted_at TIMESTAMPTZ
    )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX idx_projects_key ON project.projects(key) WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE TABLE project.project_members (
        id UUID PRIMARY KEY,
        project_id UUID NOT NULL,
        user_id UUID NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'member',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_project_member UNIQUE (project_id, user_id)
    )
        """
    )
    op.execute(
        """
        CREATE TABLE project.iterations (
        id UUID PRIMARY KEY,
        project_id UUID NOT NULL,
        name VARCHAR(200) NOT NULL,
        goal TEXT,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'planning',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        deleted_at TIMESTAMPTZ
    )
        """
    )
    op.execute(
        """
        CREATE TABLE project.requirements (
        id UUID PRIMARY KEY,
        project_id UUID NOT NULL,
        iteration_id UUID,
        title VARCHAR(500) NOT NULL,
        description TEXT,
        status VARCHAR(20) NOT NULL DEFAULT 'draft',
        priority VARCHAR(10) NOT NULL DEFAULT 'medium',
        assignee_id UUID,
        "order" INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        deleted_at TIMESTAMPTZ
    )
        """
    )
    op.execute(
        """
        CREATE TABLE project.tasks (
        id UUID PRIMARY KEY,
        project_id UUID NOT NULL,
        iteration_id UUID,
        parent_id UUID,
        title VARCHAR(500) NOT NULL,
        description TEXT,
        status VARCHAR(20) NOT NULL DEFAULT 'todo',
        priority VARCHAR(10) NOT NULL DEFAULT 'medium',
        assignee_id UUID,
        estimated_hours NUMERIC(5,1),
        logged_hours NUMERIC(5,1),
        due_date DATE,
        "order" INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        deleted_at TIMESTAMPTZ
    )
        """
    )
    op.execute(
        """
        CREATE TABLE project.bugs (
        id UUID PRIMARY KEY,
        project_id UUID NOT NULL,
        iteration_id UUID,
        title VARCHAR(500) NOT NULL,
        description TEXT,
        steps_to_reproduce TEXT,
        severity VARCHAR(10) NOT NULL DEFAULT 'medium',
        priority VARCHAR(10) NOT NULL DEFAULT 'medium',
        status VARCHAR(20) NOT NULL DEFAULT 'open',
        assignee_id UUID,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        deleted_at TIMESTAMPTZ
    )
        """
    )
    op.execute(
        """
        CREATE TABLE project.requirement_tasks (
        id UUID PRIMARY KEY,
        requirement_id UUID NOT NULL,
        task_id UUID NOT NULL,
        CONSTRAINT uq_req_task UNIQUE (requirement_id, task_id)
    )
        """
    )
    op.execute(
        """
        CREATE TABLE project.task_dependencies (
        id UUID PRIMARY KEY,
        task_id UUID NOT NULL,
        depends_on_id UUID NOT NULL,
        type VARCHAR(20) NOT NULL DEFAULT 'blocks',
        CONSTRAINT uq_task_dep UNIQUE (task_id, depends_on_id)
    )
        """
    )
    op.execute(
        """
        CREATE TABLE project.boards (
        id UUID PRIMARY KEY,
        project_id UUID NOT NULL,
        name VARCHAR(100) NOT NULL DEFAULT '默认看板',
        type VARCHAR(20) NOT NULL DEFAULT 'kanban',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
        """
    )
    op.execute(
        """
        CREATE TABLE project.board_columns (
        id UUID PRIMARY KEY,
        board_id UUID NOT NULL,
        name VARCHAR(100) NOT NULL,
        "order" INTEGER NOT NULL DEFAULT 0,
        wip_limit INTEGER,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
        """
    )
    op.execute(
        """
        CREATE TABLE project.board_swimlanes (
        id UUID PRIMARY KEY,
        board_id UUID NOT NULL,
        name VARCHAR(100) NOT NULL,
        type VARCHAR(20) NOT NULL DEFAULT 'none',
        "order" INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
        """
    )
    op.execute(
        """
        CREATE TABLE project.board_cards (
        id UUID PRIMARY KEY,
        board_id UUID NOT NULL,
        column_id UUID NOT NULL,
        swimlane_id UUID,
        item_type VARCHAR(20) NOT NULL,
        item_id UUID NOT NULL,
        "order" INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_card_item UNIQUE (board_id, item_type, item_id)
    )
        """
    )
    op.execute(
        """
        CREATE TABLE project.labels (
        id UUID PRIMARY KEY,
        project_id UUID NOT NULL,
        name VARCHAR(50) NOT NULL,
        color VARCHAR(7) NOT NULL DEFAULT '#6B7280',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        deleted_at TIMESTAMPTZ
    )
        """
    )
    op.execute(
        """
        CREATE TABLE project.item_labels (
        id UUID PRIMARY KEY,
        label_id UUID NOT NULL,
        item_type VARCHAR(20) NOT NULL,
        item_id UUID NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CONSTRAINT uq_label_item UNIQUE (label_id, item_type, item_id)
    )
        """
    )



def downgrade() -> None:
    tables = [
        "project.item_labels",
        "project.labels",
        "project.board_cards",
        "project.board_swimlanes",
        "project.board_columns",
        "project.boards",
        "project.task_dependencies",
        "project.requirement_tasks",
        "project.bugs",
        "project.tasks",
        "project.requirements",
        "project.iterations",
        "project.project_members",
        "project.projects",
        "iam.user_oauth_tokens",
        "iam.team_members",
        "iam.teams",
        "iam.user_roles",
        "iam.roles",
        "iam.users",
    ]
    for table in tables:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
