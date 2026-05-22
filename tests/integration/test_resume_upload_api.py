from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from apps.backend.app.main import app


client = TestClient(app)


def test_health_endpoint_works() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_resume_upload_creates_career_vault_profile() -> None:
    resume = Path("tests/fixtures/sample_resume_ai_consultant.txt").read_bytes()
    response = client.post("/career-vault/resume/upload", content=resume, headers={"X-Filename": "sample_resume_ai_consultant.txt"})

    assert response.status_code == 200
    body = response.json()
    assert body["parse_status"] == "parsed"
    assert body["created_profile"]["full_name"] == "Sam Patel"

