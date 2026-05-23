from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from apps.backend.app.persistence import Base


def _json_type():
    return JSON().with_variant(JSONB(), "postgresql")


class AuditLogRow(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    actor: Mapped[str] = mapped_column(String(100), default="system")
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(_json_type())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WorkflowRunRow(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    workflow_name: Mapped[str] = mapped_column(String(100), index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), index=True)
    details_json: Mapped[dict[str, Any]] = mapped_column(_json_type())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CareerProfileRow(Base):
    __tablename__ = "career_profiles"

    candidate_profile_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    upload_key: Mapped[str] = mapped_column(String(512), index=True)
    profile_json: Mapped[dict[str, Any]] = mapped_column(_json_type())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CampaignRow(Base):
    __tablename__ = "campaigns"

    campaign_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    campaign_json: Mapped[dict[str, Any]] = mapped_column(_json_type())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ModuleRegistryRow(Base):
    __tablename__ = "module_registry"

    module_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    module_json: Mapped[dict[str, Any]] = mapped_column(_json_type())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class JobRecordRow(Base):
    __tablename__ = "job_records"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    normalized_job_json: Mapped[dict[str, Any]] = mapped_column(_json_type())
    persisted_at: Mapped[str] = mapped_column(String(40))
    discovery_batch_id: Mapped[str] = mapped_column(String(64), index=True)


class JobScoreRow(Base):
    __tablename__ = "job_scores"

    job_score_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    score_json: Mapped[dict[str, Any]] = mapped_column(_json_type())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ApplicationPackageRow(Base):
    __tablename__ = "application_packages"

    application_package_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    package_json: Mapped[dict[str, Any]] = mapped_column(_json_type())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class OutreachDraftRow(Base):
    __tablename__ = "outreach_drafts"

    outreach_draft_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    gmail_draft_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    gmail_draft_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    draft_json: Mapped[dict[str, Any]] = mapped_column(_json_type())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ReviewItemRow(Base):
    __tablename__ = "review_items"

    review_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    review_json: Mapped[dict[str, Any]] = mapped_column(_json_type())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TrackerApplicationRow(Base):
    __tablename__ = "tracker_applications"

    application_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    application_json: Mapped[dict[str, Any]] = mapped_column(_json_type())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class EmailCandidateRow(Base):
    __tablename__ = "email_candidates"

    email_candidate_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    person_id: Mapped[str] = mapped_column(String(128), index=True)
    candidate_json: Mapped[dict[str, Any]] = mapped_column(_json_type())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PeopleCacheRow(Base):
    __tablename__ = "people_cache"

    application_package_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    people_json: Mapped[dict[str, Any]] = mapped_column(_json_type())


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
