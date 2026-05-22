from pathlib import Path
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core_kernel import (
    AccessDecision,
    AccessRequest,
    ApprovalDecision,
    ApprovalGate,
    AuditAction,
    AuditActorType,
    AuditEvent,
    AuditLogStore,
    ModuleDefinition,
    ModuleRegistry,
    PermissionAction,
    PermissionGrant,
    PermissionPolicy,
    WorkflowRun,
    WorkflowStatus,
    WorkflowTransition,
    WorkflowType,
)
from app.shared.contracts import (
    AuditEventPayload,
    CoreEventEnvelope,
    EventCategory,
    EventEnvelope,
    EventMetadata,
    ModuleRegistrationRequest,
    PermissionEventPayload,
    RegistryEventPayload,
    WorkflowEventPayload,
)
from app.main import app


def test_module_registry_enable_disable() -> None:
    registry = ModuleRegistry()
    module = registry.register(
        ModuleDefinition(module_key="career_vault", module_name="Career Vault", version="1.0.0")
    )

    assert registry.get("career_vault") == module
    assert registry.disable("career_vault").enabled is False
    assert registry.enable("career_vault").enabled is True


def test_audit_store_records_entries() -> None:
    store = AuditLogStore()
    entry = store.record(
        user_id=uuid4(),
        entity_type="campaign",
        entity_id=uuid4(),
        action="created",
        actor_type=AuditActorType.user,
        details_json={"source": "api"},
    )

    assert store.list() == [entry]
    assert entry.details_json["source"] == "api"


def test_permissions_and_approval_gate() -> None:
    grant = PermissionGrant(
        subject="user:1",
        resource="workflow:campaign",
        actions={PermissionAction.read, PermissionAction.approve},
    )
    policy = PermissionPolicy(subject="user:1")
    policy.grant("workflow:campaign", PermissionAction.approve)
    gate = ApprovalGate(resource="workflow:campaign", decision=ApprovalDecision.approved)
    request = AccessRequest(subject="user:1", resource="workflow:campaign", action=PermissionAction.approve)
    decision = AccessDecision(allowed=True, request=request)

    assert grant.allows(PermissionAction.approve) is True
    assert gate.can_proceed(grant.allows) is True
    assert policy.can("workflow:campaign", PermissionAction.approve) is True
    assert decision.allowed is True


def test_workflow_state_transitions() -> None:
    run = WorkflowRun(campaign_id=uuid4(), workflow_type=WorkflowType.campaign_run)

    paused = run.pause()
    resumed = paused.resume()
    completed = resumed.complete(current_node="finalize")

    assert paused.status == WorkflowStatus.paused
    assert resumed.status == WorkflowStatus.running
    assert completed.status == WorkflowStatus.completed
    assert completed.completed_at is not None


def test_event_envelope_and_registration_request() -> None:
    request = ModuleRegistrationRequest(
        module_key="campaign_planner",
        module_name="Campaign Planner",
        version="0.1.0",
    )
    envelope = EventEnvelope(
        event_type="CampaignCreated",
        source_module="campaign_planner",
        user_id=uuid4(),
        entity_type="campaign",
    )

    assert request.to_definition().module_key == "campaign_planner"
    assert envelope.event_version == "1.0"


def test_core_event_payloads_and_audit_event_conversion() -> None:
    audit_event = AuditEvent(
        actor_type=AuditActorType.system,
        action=AuditAction.created,
        entity_type="campaign",
        user_id=uuid4(),
        details_json={"source": "worker"},
    )
    entry = AuditLogStore().append_event(audit_event)
    metadata = EventMetadata(event_type="AuditLogged", event_category=EventCategory.audit, source_module="core")
    envelope = CoreEventEnvelope(
        metadata=metadata,
        payload=AuditEventPayload(
            actor_type=AuditActorType.system,
            action=AuditAction.created,
            entity_type="campaign",
            user_id=entry.user_id,
        ),
    )

    assert entry.action == "created"
    assert envelope.metadata.event_category == EventCategory.audit
    assert isinstance(
        CoreEventEnvelope(
            metadata=metadata,
            payload=PermissionEventPayload(
                subject="user:1",
                resource="workflow:campaign",
                action=PermissionAction.read,
                allowed=True,
            ),
        ).payload,
        PermissionEventPayload,
    )
    assert isinstance(
        CoreEventEnvelope(
            metadata=metadata,
            payload=WorkflowEventPayload(
                workflow_id=uuid4(),
                workflow_type=WorkflowType.campaign_run,
                to_status=WorkflowStatus.running,
            ),
        ).payload,
        WorkflowEventPayload,
    )
    assert isinstance(
        CoreEventEnvelope(
            metadata=metadata,
            payload=RegistryEventPayload(
                module_key="campaign_planner",
                module_name="Campaign Planner",
                version="1.0.0",
            ),
        ).payload,
        RegistryEventPayload,
    )


def test_terminal_workflow_requires_completed_at() -> None:
    with pytest.raises(ValueError, match="completed_at is required"):
        WorkflowRun(
            campaign_id=uuid4(),
            workflow_type=WorkflowType.scoring_run,
            status=WorkflowStatus.failed,
        )


def test_workflow_transition_marks_terminal_states() -> None:
    transition = WorkflowTransition(
        workflow_id=uuid4(),
        workflow_type=WorkflowType.people_run,
        from_status=WorkflowStatus.running,
        to_status=WorkflowStatus.completed,
    )

    assert transition.is_terminal() is True


def test_fastapi_app_includes_core_routes() -> None:
    route_paths = {getattr(route, "path", None) for route in app.routes}

    assert "/health" in route_paths
    assert "/campaigns/create" in route_paths
    assert "/career-vault/resume/upload" in route_paths
