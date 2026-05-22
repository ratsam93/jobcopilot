from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.modules.career_vault.api import router as career_router
from app.modules.campaign_planner.api import router


app = FastAPI()
app.include_router(career_router)
app.include_router(router)
client = TestClient(app)


def _create_profile() -> str:
    response = client.post(
        "/career-vault/resume/upload",
        content=b"Sam Doe\nsam@example.com\nRemote USA\n- Built Python FastAPI backend services\n- React and Typescript",
        headers={"X-Filename": "resume.txt", "Content-Type": "application/octet-stream"},
    )
    return response.json()["candidate_profile_id"]


def test_campaign_creation_parse_status_and_jobs():
    profile_id = _create_profile()
    response = client.post(
        "/campaigns/create",
        json={
            "candidate_profile_id": profile_id,
            "natural_language_prompt": "Apply to top US tech companies where I fit",
        },
    )
    assert response.status_code == 200
    campaign = response.json()
    assert campaign["execution_mode"] == "approval_required"
    assert campaign["structured_query"]["target_countries"] == ["United States"]

    parsed = client.post(f"/campaigns/{campaign['campaign_id']}/parse", json={})
    assert parsed.status_code == 200
    assert parsed.json()["status"] == "parsed"

    status = client.get(f"/campaigns/{campaign['campaign_id']}/status")
    assert status.status_code == 200
    assert status.json()["status"] == "parsed"
    assert status.json()["job_count"] == 0
    assert status.json()["structured_query"]["target_countries"] == ["United States"]

    run = client.post(f"/campaigns/{campaign['campaign_id']}/run")
    assert run.status_code == 200
    jobs = client.get(f"/campaigns/{campaign['campaign_id']}/jobs")
    assert jobs.status_code == 200
    assert len(jobs.json()) == 2
    assert jobs.json()[0]["status"] == "queued"


def test_campaign_validation_rejects_empty_targeting():
    profile_id = _create_profile()
    response = client.post(
        "/campaigns/create",
        json={
            "candidate_profile_id": profile_id,
            "natural_language_prompt": "Apply broadly",
        },
    )
    assert response.status_code == 422
