from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class WorkflowType(str, Enum):
    campaign_run = "campaign_run"
    scoring_run = "scoring_run"
    people_run = "people_run"


class WorkflowStatus(str, Enum):
    running = "running"
    paused = "paused"
    failed = "failed"
    completed = "completed"
    cancelled = "cancelled"


class WorkflowRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    campaign_id: UUID
    workflow_type: WorkflowType
    status: WorkflowStatus = WorkflowStatus.running
    current_node: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    error_json: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_status_fields(self) -> "WorkflowRun":
        if self.status in {WorkflowStatus.completed, WorkflowStatus.failed, WorkflowStatus.cancelled}:
            if self.completed_at is None:
                raise ValueError("completed_at is required for terminal workflows")
        return self

    def pause(self) -> "WorkflowRun":
        if self.status != WorkflowStatus.running:
            raise ValueError("only running workflows can be paused")
        return self.model_copy(update={"status": WorkflowStatus.paused})

    def resume(self) -> "WorkflowRun":
        if self.status != WorkflowStatus.paused:
            raise ValueError("only paused workflows can be resumed")
        return self.model_copy(update={"status": WorkflowStatus.running})

    def cancel(self) -> "WorkflowRun":
        if self.status in {WorkflowStatus.completed, WorkflowStatus.cancelled}:
            raise ValueError("terminal workflows cannot be cancelled")
        return self.model_copy(
            update={
                "status": WorkflowStatus.cancelled,
                "completed_at": datetime.now(timezone.utc),
            }
        )

    def complete(self, current_node: str | None = None) -> "WorkflowRun":
        if self.status in {WorkflowStatus.completed, WorkflowStatus.cancelled}:
            raise ValueError("terminal workflows cannot be completed twice")
        return self.model_copy(
            update={
                "status": WorkflowStatus.completed,
                "current_node": current_node,
                "completed_at": datetime.now(timezone.utc),
            }
        )


class WorkflowTransition(BaseModel):
    workflow_id: UUID
    workflow_type: WorkflowType
    from_status: WorkflowStatus
    to_status: WorkflowStatus
    actor_id: UUID | None = None
    details_json: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def is_terminal(self) -> bool:
        return self.to_status in {
            WorkflowStatus.completed,
            WorkflowStatus.failed,
            WorkflowStatus.cancelled,
        }
