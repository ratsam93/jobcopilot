from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from apps.backend.app.core_kernel.audit import AuditAction, AuditActorType
from apps.backend.app.core_kernel.permissions import PermissionAction
from apps.backend.app.core_kernel.registry import ModuleDefinition
from apps.backend.app.core_kernel.workflow_state import WorkflowStatus, WorkflowType


class EventType(str, Enum):
    campaign_created = "CampaignCreated"
    workflow_started = "WorkflowStarted"
    workflow_paused = "WorkflowPaused"
    workflow_resumed = "WorkflowResumed"
    workflow_cancelled = "WorkflowCancelled"
    audit_logged = "AuditLogged"


class EventEnvelope(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    event_version: str = "1.0"
    source_module: str
    user_id: UUID
    campaign_id: UUID | None = None
    entity_type: str
    entity_id: UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: UUID | None = None
    causation_id: UUID | None = None


class EventCategory(str, Enum):
    core = "core"
    audit = "audit"
    workflow = "workflow"
    registry = "registry"


class EventMetadata(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    event_version: str = "1.0"
    event_category: EventCategory = EventCategory.core
    source_module: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: UUID | None = None
    causation_id: UUID | None = None


class AuditEventPayload(BaseModel):
    actor_type: AuditActorType
    action: AuditAction
    entity_type: str
    entity_id: UUID | None = None
    user_id: UUID
    details_json: dict[str, Any] = Field(default_factory=dict)


class PermissionEventPayload(BaseModel):
    subject: str
    resource: str
    action: PermissionAction
    allowed: bool
    reason: str | None = None


class WorkflowEventPayload(BaseModel):
    workflow_id: UUID
    workflow_type: WorkflowType
    from_status: WorkflowStatus | None = None
    to_status: WorkflowStatus
    details_json: dict[str, Any] = Field(default_factory=dict)


class RegistryEventPayload(BaseModel):
    module_key: str
    module_name: str
    version: str
    enabled: bool = True
    config_json: dict[str, Any] = Field(default_factory=dict)


class ModuleRegistrationRequest(BaseModel):
    module_key: str
    module_name: str
    version: str
    enabled: bool = True
    config_json: dict[str, Any] = Field(default_factory=dict)

    def to_definition(self) -> ModuleDefinition:
        return ModuleDefinition(
            module_key=self.module_key,
            module_name=self.module_name,
            version=self.version,
            enabled=self.enabled,
            config_json=self.config_json,
        )


class ModuleRegistrationResponse(ModuleDefinition):
    pass


class WorkflowTransitionRequest(BaseModel):
    workflow_type: WorkflowType
    target_status: WorkflowStatus
    current_node: str | None = None


class CoreEventEnvelope(BaseModel):
    metadata: EventMetadata
    payload: (
        AuditEventPayload
        | PermissionEventPayload
        | WorkflowEventPayload
        | RegistryEventPayload
    )


class ResumeParseResult(BaseModel):
    candidate_profile_id: UUID
    parse_status: str
    source_filename: str
    extracted_text: str
    created_profile: dict[str, Any]
    duplicate_of: UUID | None = None


class JobParseResult(BaseModel):
    job_id: str
    title: str
    company: str
    source: str
    source_url: str
    canonical_url: str
    location: str | None = None
    remote: bool = False
    description: str = ""
    salary_min_usd: int | None = None
    salary_max_usd: int | None = None
    required_skills: list[str] = Field(default_factory=list)
    dedup_key: str


class FitScoreResult(BaseModel):
    job_score_id: str
    job_id: str
    candidate_profile_id: str
    fit_score: int
    decision: str
    component_scores: dict[str, int]
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    explanation: str
    confidence: float


class CompanyResearchResult(BaseModel):
    company_name: str
    source_url: str
    summary: str
    signals: list[str] = Field(default_factory=list)
    hiring_teams: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class ResumeTailoringResult(BaseModel):
    application_package_id: str
    job_id: str
    candidate_profile_id: str
    fit_summary: list[str] = Field(default_factory=list)
    unsupported_claims_detected: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    status: str
    resume_version: dict[str, Any]
    cover_letter: str


class CoverLetterResult(BaseModel):
    subject: str
    body: str
    tone: str = "professional"
    personalization_points: list[str] = Field(default_factory=list)


class OutreachEmailResult(BaseModel):
    outreach_draft_id: str
    application_package_id: str
    person_id: str
    channel: str
    draft_type: str
    subject: str
    body: str
    personalization_points: list[str] = Field(default_factory=list)
    status: str
    gmail_draft: dict[str, str] | None = None


class ReviewQueueItem(BaseModel):
    review_id: str
    user_id: str
    entity_type: str
    entity_id: str
    status: str
    requested_at: str
    reviewed_at: str | None = None
    review_notes: str | None = None
