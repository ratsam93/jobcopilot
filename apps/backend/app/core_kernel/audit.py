from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from apps.backend.app.persistence_repos import AuditLogRepository


class AuditActorType(str, Enum):
    user = "user"
    system = "system"
    admin = "admin"
    worker = "worker"


class AuditLogEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    entity_type: str
    entity_id: UUID | None = None
    action: str
    actor_type: AuditActorType
    details_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditAction(str, Enum):
    created = "created"
    updated = "updated"
    deleted = "deleted"
    approved = "approved"
    rejected = "rejected"
    transitioned = "transitioned"
    accessed = "accessed"


class AuditEvent(BaseModel):
    actor_type: AuditActorType
    action: AuditAction
    entity_type: str
    entity_id: UUID | None = None
    user_id: UUID
    details_json: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_entry(self) -> AuditLogEntry:
        return AuditLogEntry(
            user_id=self.user_id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            action=self.action.value,
            actor_type=self.actor_type,
            details_json=self.details_json,
            created_at=self.occurred_at,
        )


class AuditLogStore:
    def __init__(self) -> None:
        self.repo = AuditLogRepository()

    def append(self, entry: AuditLogEntry) -> AuditLogEntry:
        self.repo.append(entry.model_dump(mode="json"))
        return entry

    def append_event(self, event: AuditEvent) -> AuditLogEntry:
        return self.append(event.to_entry())

    def record(
        self,
        *,
        user_id: UUID,
        entity_type: str,
        action: str,
        actor_type: AuditActorType,
        entity_id: UUID | None = None,
        details_json: dict[str, Any] | None = None,
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_type=actor_type,
            details_json=details_json or {},
        )
        return self.append(entry)

    def list(self) -> list[AuditLogEntry]:
        return [AuditLogEntry.model_validate(item) for item in self.repo.list()]
