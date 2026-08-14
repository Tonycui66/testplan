"""add webhook dedupe unique index

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-15
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_webhook_dedupe "
        "ON repo.webhook_events (connection_id, dedupe_key) WHERE dedupe_key IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS repo.uq_webhook_dedupe")
