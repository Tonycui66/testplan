"""add webhook dedupe key

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-15
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE repo.webhook_events ADD COLUMN IF NOT EXISTS dedupe_key VARCHAR(255)")


def downgrade() -> None:
    op.execute("ALTER TABLE repo.webhook_events DROP COLUMN IF EXISTS dedupe_key")
