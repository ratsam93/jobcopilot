"""add workflow_runs updated_at

Revision ID: 0003_workflow_runs_updated_at
Revises: 0002_add_remaining_persistence_tables
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_workflow_runs_updated_at"
down_revision = "0002_add_remaining_persistence_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workflow_runs",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    op.drop_column("workflow_runs", "updated_at")
