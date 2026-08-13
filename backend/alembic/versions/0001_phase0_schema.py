"""create Phase 0 schemas

Revision ID: 0001
Revises:
Create Date: 2026-08-13
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SCHEMAS = [
    "iam",
    "project",
    "repo",
    "pipeline",
    "artifact",
    "test",
    "deploy",
    "metrics",
    "notification",
]


def upgrade() -> None:
    for schema in SCHEMAS:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")


def downgrade() -> None:
    for schema in reversed(SCHEMAS):
        op.execute(f"DROP SCHEMA IF EXISTS {schema}")
