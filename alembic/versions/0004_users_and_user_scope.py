"""add users and user scope columns

Revision ID: 0004_users_and_user_scope
Revises: 0003_workflow_runs_updated_at
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004_users_and_user_scope"
down_revision = "0003_workflow_runs_updated_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    for table in [
        "audit_logs",
        "workflow_runs",
        "career_profiles",
        "campaigns",
        "module_registry",
        "job_records",
        "job_scores",
        "application_packages",
        "outreach_drafts",
        "review_items",
        "tracker_applications",
        "email_candidates",
        "people_cache",
    ]:
        op.add_column(table, sa.Column("user_id", sa.String(length=36), nullable=True))
        op.create_index(f"ix_{table}_user_id", table, ["user_id"])


def downgrade() -> None:
    for table in [
        "people_cache",
        "email_candidates",
        "tracker_applications",
        "review_items",
        "outreach_drafts",
        "application_packages",
        "job_scores",
        "job_records",
        "module_registry",
        "campaigns",
        "career_profiles",
        "workflow_runs",
        "audit_logs",
    ]:
        op.drop_index(f"ix_{table}_user_id", table_name=table)
        op.drop_column(table, "user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
