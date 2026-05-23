from __future__ import annotations

from fastapi.testclient import TestClient

from apps.backend.app.main import app
from apps.backend.app.workflow_runs import workflow_runs


client = TestClient(app)


def test_campaign_run_enqueues_worker_task(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    def fake_delay(campaign_id: str, workflow_run_id: str) -> object:
        calls.append((campaign_id, workflow_run_id))
        return object()

    monkeypatch.setattr("apps.backend.app.modules.campaign_planner.api.enqueue_run_campaign.delay", fake_delay)

    create_response = client.post(
        "/api/campaigns/create",
        json={
            "natural_language_prompt": "Apply to top technology companies across the USA where I fit.",
            "campaign_name": None,
            "execution_mode": "approval_required",
        },
    )
    campaign_id = create_response.json()["campaign_id"]

    response = client.post(f"/api/campaigns/{campaign_id}/run")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"
    assert body["campaign_id"] == campaign_id
    assert body["workflow_run_id"]
    assert calls == [(campaign_id, body["workflow_run_id"])]

    stored = workflow_runs.get(body["workflow_run_id"])
    assert stored is not None
    assert stored["workflow_name"] == "run_campaign"
    assert stored["status"] == "queued"
