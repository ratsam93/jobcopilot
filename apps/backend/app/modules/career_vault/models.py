from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResumeSource(BaseModel):
    filename: str
    content_type: str | None = None
    text: str
    uploaded_at: datetime = Field(default_factory=utc_now)


class Skill(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    candidate_profile_id: UUID
    skill_name: str
    skill_category: str = "general"
    evidence_text: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.75)
    approved: bool = True
    source: str = "resume"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Claim(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    candidate_profile_id: UUID
    claim_text: str
    claim_type: str = "experience"
    source: str = "resume"
    approved: bool = True
    can_use_in_resume: bool = True
    can_use_in_email: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class DoNotClaim(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    candidate_profile_id: UUID
    blocked_claim: str
    reason: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class Bullet(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    candidate_profile_id: UUID
    bullet_text: str
    category: str = "general"
    role_track: str | None = None
    evidence_source: str | None = None
    approved: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class CareerProfile(BaseModel):
    candidate_profile_id: UUID = Field(default_factory=uuid4)
    user_id: UUID | None = None
    full_name: str | None = None
    primary_email: str | None = None
    phone: str | None = None
    location: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    salary_preferences: dict[str, int | None] = Field(default_factory=dict)
    location_preferences: list[str] = Field(default_factory=list)
    remote_preferences: list[str] = Field(default_factory=list)
    role_track: str | None = None
    career_story: str | None = None
    version: int = 1
    active: bool = True
    source_resumes: list[ResumeSource] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    approved_claims: list[Claim] = Field(default_factory=list)
    do_not_claim: list[DoNotClaim] = Field(default_factory=list)
    bullet_bank: list[Bullet] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ClaimInput(BaseModel):
    claim_text: str
    claim_type: str = "experience"
    can_use_in_resume: bool = True
    can_use_in_email: bool = True


class DoNotClaimInput(BaseModel):
    blocked_claim: str
    reason: str | None = None


class BulletInput(BaseModel):
    bullet_text: str
    category: str = "general"
    role_track: str | None = None
    evidence_source: str | None = None


class SkillInput(BaseModel):
    skill_name: str
    skill_category: str = "general"
    evidence_text: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.75)


class ProfileUpdateInput(BaseModel):
    full_name: str | None = None
    primary_email: str | None = None
    phone: str | None = None
    location: str | None = None
    target_roles: list[str] | None = None
    salary_preferences: dict[str, int | None] | None = None
    location_preferences: list[str] | None = None
    remote_preferences: list[str] | None = None
    role_track: str | None = None
    career_story: str | None = None


class ResumeUploadResult(BaseModel):
    candidate_profile_id: UUID
    parse_status: Literal["parsed", "failed"]
    source_filename: str
    extracted_text: str
    created_profile: CareerProfile
    duplicate_of: UUID | None = None
