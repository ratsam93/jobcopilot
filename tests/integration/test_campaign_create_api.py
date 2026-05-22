from __future__ import annotations

from fastapi.testclient import TestClient

from apps.backend.app.main import app


client = TestClient(app)


def test_campaign_create_parses_structured_query() -> None:
    response = client.post(
        "/api/campaigns/create",
        json={
            "natural_language_prompt": "Apply to top technology companies across the USA where I fit.",
            "campaign_name": None,
            "execution_mode": "approval_required",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "created"
    assert body["structured_query"]["target_countries"] == ["United States"]
    assert body["execution_mode"] == "approval_required"
