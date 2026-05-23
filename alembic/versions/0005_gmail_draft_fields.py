"""add gmail draft fields

Revision ID: 0005_gmail_draft_fields
Revises: 0004_users_and_user_scope
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005_gmail_draft_fields"
down_revision = "0004_users_and_user_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("outreach_drafts", sa.Column("gmail_draft_id", sa.String(length=128), nullable=True))
    op.add_column("outreach_drafts", sa.Column("gmail_draft_status", sa.String(length=50), nullable=True))
    op.create_index("ix_outreach_drafts_gmail_draft_id", "outreach_drafts", ["gmail_draft_id"])


def downgrade() -> None:
    op.drop_index("ix_outreach_drafts_gmail_draft_id", table_name="outreach_drafts")
    op.drop_column("outreach_drafts", "gmail_draft_status")
    op.drop_column("outreach_drafts", "gmail_draft_id")
