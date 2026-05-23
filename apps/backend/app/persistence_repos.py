from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from apps.backend.app.models import (
    ApplicationPackageRow,
    AuditLogRow,
    EmailCandidateRow,
    JobRecordRow,
    JobScoreRow,
    ModuleRegistryRow,
    OutreachDraftRow,
    PeopleCacheRow,
    ReviewItemRow,
    TrackerApplicationRow,
    WorkflowRunRow,
)
from apps.backend.app.persistence import session_scope


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class JsonStoreRepository:
    row_type: Any
    key_field: str
    payload_field: str

    def upsert(self, key: str, payload: dict[str, Any], **extra: Any) -> dict[str, Any]:
        with session_scope() as session:
            row = session.get(self.row_type, key)
            if row is None:
                row = self.row_type(**{self.key_field: key, self.payload_field: payload, **extra})
                session.add(row)
            else:
                setattr(row, self.payload_field, payload)
                for field, value in extra.items():
                    setattr(row, field, value)
            return payload

    def get(self, key: str) -> dict[str, Any] | None:
        with session_scope() as session:
            row = session.get(self.row_type, key)
            if row is None:
                return None
            return getattr(row, self.payload_field)

    def list_all(self) -> list[dict[str, Any]]:
        with session_scope() as session:
            rows = session.execute(select(self.row_type)).scalars().all()
            return [getattr(row, self.payload_field) for row in rows]


class ModuleRegistryRepository(JsonStoreRepository):
    def __init__(self) -> None:
        super().__init__(ModuleRegistryRow, "module_key", "module_json")


class JobRecordRepository(JsonStoreRepository):
    def __init__(self) -> None:
        super().__init__(JobRecordRow, "job_id", "normalized_job_json")


class JobScoreRepository(JsonStoreRepository):
    def __init__(self) -> None:
        super().__init__(JobScoreRow, "job_score_id", "score_json")


class ApplicationPackageRepository(JsonStoreRepository):
    def __init__(self) -> None:
        super().__init__(ApplicationPackageRow, "application_package_id", "package_json")


class OutreachDraftRepository(JsonStoreRepository):
    def __init__(self) -> None:
        super().__init__(OutreachDraftRow, "outreach_draft_id", "draft_json")

    def mark_gmail_draft(self, outreach_draft_id: str, gmail_draft_id: str, gmail_draft_status: str, gmail_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        with session_scope() as session:
            row = session.get(self.row_type, outreach_draft_id)
            if row is None:
                raise KeyError(outreach_draft_id)
            row.gmail_draft_id = gmail_draft_id
            row.gmail_draft_status = gmail_draft_status
            if gmail_payload is not None:
                payload = dict(row.draft_json)
                payload["gmail_draft"] = gmail_payload
                row.draft_json = payload
            return {
                "outreach_draft_id": row.outreach_draft_id,
                "gmail_draft_id": row.gmail_draft_id,
                "gmail_draft_status": row.gmail_draft_status,
                "draft_json": row.draft_json,
                "created_at": row.created_at,
            }


class ReviewItemRepository(JsonStoreRepository):
    def __init__(self) -> None:
        super().__init__(ReviewItemRow, "review_id", "review_json")


class TrackerApplicationRepository(JsonStoreRepository):
    def __init__(self) -> None:
        super().__init__(TrackerApplicationRow, "application_id", "application_json")


class EmailCandidateRepository(JsonStoreRepository):
    def __init__(self) -> None:
        super().__init__(EmailCandidateRow, "email_candidate_id", "candidate_json")

    def upsert(self, key: str, payload: dict[str, Any], **extra: Any) -> dict[str, Any]:
        person_id = extra.get("person_id", payload.get("person_id"))
        if person_id is None:
            raise ValueError("email candidate payload requires person_id")
        with session_scope() as session:
            row = session.get(self.row_type, key)
            if row is None:
                row = self.row_type(
                    **{
                        self.key_field: key,
                        "person_id": person_id,
                        self.payload_field: payload,
                    }
                )
                session.add(row)
            else:
                setattr(row, "person_id", person_id)
                setattr(row, self.payload_field, payload)
            return payload


class PeopleCacheRepository(JsonStoreRepository):
    def __init__(self) -> None:
        super().__init__(PeopleCacheRow, "application_package_id", "people_json")


class AuditLogRepository:
    def append(self, payload: dict[str, Any]) -> dict[str, Any]:
        with session_scope() as session:
            row = AuditLogRow(
                id=payload["id"],
                event_type=payload["event_type"],
                actor=payload.get("actor", "system"),
                payload_json=payload,
                created_at=payload.get("created_at", _utcnow()),
            )
            session.add(row)
            return payload

    def list(self) -> list[dict[str, Any]]:
        with session_scope() as session:
            rows = session.execute(select(AuditLogRow)).scalars().all()
            return [row.payload_json for row in rows]


class WorkflowRunRepository:
    def create(self, workflow_name: str, status: str, details: dict[str, Any]) -> dict[str, Any]:
        with session_scope() as session:
            row = WorkflowRunRow(workflow_name=workflow_name, status=status, details_json=details)
            session.add(row)
            session.flush()
            return {
                "id": row.id,
                "workflow_name": row.workflow_name,
                "status": row.status,
                "details_json": row.details_json,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }

    def update(self, run_id: str, status: str, details: dict[str, Any]) -> dict[str, Any]:
        with session_scope() as session:
            row = session.get(WorkflowRunRow, run_id)
            if row is None:
                raise KeyError(run_id)
            row.status = status
            row.details_json = details
            session.flush()
            return {
                "id": run_id,
                "workflow_name": row.workflow_name,
                "status": status,
                "details_json": details,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }

    def get(self, run_id: str) -> dict[str, Any] | None:
        with session_scope() as session:
            row = session.get(WorkflowRunRow, run_id)
            if row is None:
                return None
            return {
                "id": row.id,
                "workflow_name": row.workflow_name,
                "status": row.status,
                "details_json": row.details_json,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
