from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


ExecutionMode = Literal["research_only", "draft_only", "approval_required", "manual_execution"]
CampaignStatus = Literal["created", "parsed", "running", "paused", "cancelled", "completed", "failed"]
RunStatus = Literal["pending", "running", "paused", "cancelled", "completed", "failed"]


class StructuredQuery(BaseModel):
    target_countries: list[str] = Field(default_factory=list)
    target_locations: list[str] = Field(default_factory=list)
    company_types: list[str] = Field(default_factory=list)
    company_quality: str = "top_or_high_growth"
    role_tracks: list[str] = Field(default_factory=list)
    exclude_roles: list[str] = Field(default_factory=list)
    minimum_fit_score: int = Field(default=75, ge=0, le=100)
    salary: dict[str, int | None] = Field(default_factory=dict)
    include_internal_people: bool = True
    include_email_discovery: bool = True
    include_cover_letter: bool = True
    include_resume_tailoring: bool = True


class CampaignCreateInput(BaseModel):
    user_id: UUID | None = None
    candidate_profile_id: UUID | None = None
    natural_language_prompt: str
    campaign_name: str | None = None
    execution_mode: ExecutionMode | None = None


class ParsedCampaign(BaseModel):
    campaign_id: UUID
    user_id: UUID | None = None
    candidate_profile_id: UUID | None = None
    natural_language_prompt: str
    campaign_name: str
    structured_query: StructuredQuery
    execution_mode: ExecutionMode = "approval_required"
    status: CampaignStatus = "created"


class Campaign(ParsedCampaign):
    constraints: list["CampaignConstraint"] = Field(default_factory=list)
    runs: list["CampaignRun"] = Field(default_factory=list)
    jobs: list["JobSummary"] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CampaignConstraint(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    campaign_id: UUID
    constraint_type: str
    constraint_value: str
    mandatory: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class CampaignRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    campaign_id: UUID
    run_type: str = "discovery"
    status: RunStatus = "pending"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_json: dict[str, object] | None = None


class JobSummary(BaseModel):
    job_id: UUID
    campaign_id: UUID
    title: str
    company_name: str
    source: str | None = None
    source_url: str | None = None
    location: str | None = None
    remote: bool = False
    fit_score: float | None = None
    reason: str | None = None
    status: str = "queued"


class CampaignParseInput(BaseModel):
    natural_language_prompt: str | None = None


class ManualJobInput(BaseModel):
    company_name: str
    role_title: str
    source: str = "manual"
    source_url: str | None = None
    location: str | None = None
    remote: bool = False
    description: str = ""
    required_skills: list[str] = Field(default_factory=list)
