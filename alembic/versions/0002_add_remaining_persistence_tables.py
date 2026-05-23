"""add remaining persistence tables

Revision ID: 0002_add_remaining_persistence_tables
Revises: 0001_initial_schema
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_add_remaining_persistence_tables"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "module_registry",
        sa.Column("module_key", sa.String(length=100), primary_key=True),
        sa.Column("module_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "job_records",
        sa.Column("job_id", sa.String(length=64), primary_key=True),
        sa.Column("normalized_job_json", sa.JSON(), nullable=False),
        sa.Column("persisted_at", sa.String(length=40), nullable=False),
        sa.Column("discovery_batch_id", sa.String(length=64), nullable=False),
    )
    op.create_index("ix_job_records_discovery_batch_id", "job_records", ["discovery_batch_id"])

    op.create_table(
        "job_scores",
        sa.Column("job_score_id", sa.String(length=64), primary_key=True),
        sa.Column("score_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "application_packages",
        sa.Column("application_package_id", sa.String(length=64), primary_key=True),
        sa.Column("package_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "outreach_drafts",
        sa.Column("outreach_draft_id", sa.String(length=128), primary_key=True),
        sa.Column("draft_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "review_items",
        sa.Column("review_id", sa.String(length=128), primary_key=True),
        sa.Column("review_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "tracker_applications",
        sa.Column("application_id", sa.String(length=128), primary_key=True),
        sa.Column("application_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "email_candidates",
        sa.Column("email_candidate_id", sa.String(length=128), primary_key=True),
        sa.Column("person_id", sa.String(length=128), nullable=False),
        sa.Column("candidate_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_email_candidates_person_id", "email_candidates", ["person_id"])

    op.create_table(
        "people_cache",
        sa.Column("application_package_id", sa.String(length=128), primary_key=True),
        sa.Column("people_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("people_cache")
    op.drop_index("ix_email_candidates_person_id", table_name="email_candidates")
    op.drop_table("email_candidates")
    op.drop_table("tracker_applications")
    op.drop_table("review_items")
    op.drop_table("outreach_drafts")
    op.drop_table("application_packages")
    op.drop_table("job_scores")
    op.drop_index("ix_job_records_discovery_batch_id", table_name="job_records")
    op.drop_table("job_records")
    op.drop_table("module_registry")
