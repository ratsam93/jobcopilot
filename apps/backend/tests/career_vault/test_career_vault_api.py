from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.modules.career_vault.api import router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_resume_upload_creates_profile_and_claims():
    response = client.post(
        "/career-vault/resume/upload",
        content=b"Sam Doe\nsam@example.com\n+1 555 123 4567\nRemote India\n- Built FastAPI services\n- Python and SQL",
        headers={"X-Filename": "resume.txt", "Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["parse_status"] == "parsed"
    assert payload["created_profile"]["primary_email"] == "sam@example.com"
    assert payload["created_profile"]["skills"]
    assert payload["created_profile"]["approved_claims"]


def test_profile_update_claims_and_do_not_claim():
    upload = client.post(
        "/career-vault/resume/upload",
        content=b"Sam Doe\nsam@example.com\nRemote USA\n- Led backend APIs",
        headers={"X-Filename": "resume.txt", "Content-Type": "application/octet-stream"},
    ).json()
    profile_id = upload["candidate_profile_id"]

    update = client.post(
        f"/career-vault/profile/{profile_id}/update",
        json={"target_roles": ["backend engineer"], "career_story": "Backend builder"},
    )
    assert update.status_code == 200
    claim = client.post(
        f"/career-vault/profile/{profile_id}/approved-claims",
        json={"claim_text": "Led backend APIs", "claim_type": "experience"},
    )
    assert claim.status_code == 200
    blocked = client.post(
        f"/career-vault/profile/{profile_id}/do-not-claim",
        json={"blocked_claim": "Managed Salesforce", "reason": "Not verified"},
    )
    assert blocked.status_code == 200
    duplicate_claim = client.post(
        f"/career-vault/profile/{profile_id}/approved-claims",
        json={"claim_text": "Led backend APIs", "claim_type": "experience"},
    )
    assert duplicate_claim.status_code == 200
    assert duplicate_claim.json()["id"] == claim.json()["id"]
    profile = client.get(f"/career-vault/profile/{profile_id}").json()
    assert profile["profile"]["target_roles"] == ["backend engineer"]
    assert profile["approved_claims"]
    assert profile["do_not_claim"]
