"""Allow contacts change requests

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-19 20:20:00.000000
"""
from __future__ import annotations

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE change_request_section ADD VALUE IF NOT EXISTS 'contacts'"
    )


def downgrade() -> None:
    # PostgreSQL does not support removing enum values safely without rebuilding the type.
    pass
