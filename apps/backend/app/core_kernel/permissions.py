from __future__ import annotations

from enum import Enum
from typing import Callable
from uuid import UUID

from pydantic import BaseModel, Field


class PermissionAction(str, Enum):
    read = "read"
    create = "create"
    update = "update"
    delete = "delete"
    approve = "approve"
    pause = "pause"
    resume = "resume"
    cancel = "cancel"


class PermissionGrant(BaseModel):
    subject: str
    resource: str
    actions: set[PermissionAction] = Field(default_factory=set)

    def allows(self, action: PermissionAction) -> bool:
        return action in self.actions

    def allows_any(self, *actions: PermissionAction) -> bool:
        return any(self.allows(action) for action in actions)


class PermissionPolicy(BaseModel):
    subject: str
    grants: list[PermissionGrant] = Field(default_factory=list)

    def can(self, resource: str, action: PermissionAction) -> bool:
        return any(
            grant.resource == resource and grant.allows(action) and grant.subject == self.subject
            for grant in self.grants
        )

    def grant(self, resource: str, *actions: PermissionAction) -> PermissionGrant:
        grant = PermissionGrant(subject=self.subject, resource=resource, actions=set(actions))
        self.grants.append(grant)
        return grant

    def resources_for(self, action: PermissionAction) -> set[str]:
        return {
            grant.resource
            for grant in self.grants
            if grant.subject == self.subject and grant.allows(action)
        }


class ApprovalDecision(str, Enum):
    approved = "approved"
    rejected = "rejected"
    pending = "pending"


class ApprovalGate(BaseModel):
    resource: str
    required_action: PermissionAction = PermissionAction.approve
    decision: ApprovalDecision = ApprovalDecision.pending
    reason: str | None = None

    def can_proceed(self, permission_check: Callable[[PermissionAction], bool]) -> bool:
        return self.decision == ApprovalDecision.approved and permission_check(self.required_action)


class AccessRequest(BaseModel):
    subject: str
    resource: str
    action: PermissionAction
    trace_id: UUID | None = None


class AccessDecision(BaseModel):
    allowed: bool
    reason: str | None = None
    request: AccessRequest
