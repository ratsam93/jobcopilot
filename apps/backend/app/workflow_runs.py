from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from apps.backend.app.persistence_repos import WorkflowRunRepository


class WorkflowRunService:
    def __init__(self) -> None:
        self.repo = WorkflowRunRepository()

    def create(self, workflow_name: str, details: dict[str, object] | None = None) -> dict[str, object]:
        return self.repo.create(
            workflow_name=workflow_name,
            status="queued",
            details=details or {},
        )

    def mark_started(self, run_id: str, details: dict[str, object] | None = None) -> dict[str, object]:
        current = self.repo.get(run_id) or {}
        payload = {**(current.get("details_json") or {}), **(details or {}), "started_at": self._now()}
        return self.repo.update(run_id, "running", payload)

    def mark_succeeded(self, run_id: str, details: dict[str, object] | None = None) -> dict[str, object]:
        current = self.repo.get(run_id) or {}
        payload = {**(current.get("details_json") or {}), **(details or {}), "completed_at": self._now()}
        return self.repo.update(run_id, "completed", payload)

    def mark_failed(self, run_id: str, error: str, details: dict[str, object] | None = None) -> dict[str, object]:
        current = self.repo.get(run_id) or {}
        payload = {
            **(current.get("details_json") or {}),
            **(details or {}),
            "error": error,
            "failed_at": self._now(),
        }
        return self.repo.update(run_id, "failed", payload)

    def get(self, run_id: str) -> dict[str, object] | None:
        return self.repo.get(run_id)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


workflow_runs = WorkflowRunService()
