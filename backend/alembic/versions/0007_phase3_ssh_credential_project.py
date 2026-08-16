"""add project ownership to ssh credentials

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-16
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE deploy.ssh_credentials ADD COLUMN IF NOT EXISTS project_id UUID")


def downgrade() -> None:
    op.execute("ALTER TABLE deploy.ssh_credentials DROP COLUMN IF EXISTS project_id")
