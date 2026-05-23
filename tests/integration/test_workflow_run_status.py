from __future__ import annotations

from apps.backend.app.workflow_runs import workflow_runs


def test_workflow_run_status_and_errors_persist() -> None:
    created = workflow_runs.create("run_campaign", {"campaign_id": "campaign-1"})
    run_id = created["id"]

    started = workflow_runs.mark_started(run_id, {"step": "discover_jobs"})
    assert started["status"] == "running"
    assert started["details_json"]["step"] == "discover_jobs"

    failed = workflow_runs.mark_failed(run_id, "boom", {"step": "discover_jobs"})
    assert failed["status"] == "failed"
    assert failed["details_json"]["error"] == "boom"
    assert failed["details_json"]["step"] == "discover_jobs"
