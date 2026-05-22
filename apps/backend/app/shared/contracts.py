from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.core_kernel.audit import AuditAction, AuditActorType
from app.core_kernel.permissions import PermissionAction
from app.core_kernel.registry import ModuleDefinition
from app.core_kernel.workflow_state import WorkflowStatus, WorkflowType


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
