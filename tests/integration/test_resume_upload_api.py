from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import inspect

from apps.backend.app.db_init import initialize_database
from apps.backend.app.main import app
from apps.backend.app.persistence import engine


client = TestClient(app)


def test_health_endpoint_works() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_dependency_health_endpoint_reports_runtime_settings() -> None:
    response = client.get("/health/dependencies")
    assert response.status_code == 200
    body = response.json()
    assert body["app_env"] == "development"
    assert body["database_url"].startswith("sqlite:///")
    assert body["redis_url"].startswith("redis://")


def test_database_health_endpoint_works_with_default_database() -> None:
    response = client.get("/health/database")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_database_tables_are_initialized() -> None:
    initialize_database()
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert "audit_logs" in tables
    assert "workflow_runs" in tables


def test_resume_upload_creates_career_vault_profile() -> None:
    resume = Path("tests/fixtures/sample_resume_ai_consultant.txt").read_bytes()
    response = client.post("/api/career-vault/resume/upload", content=resume, headers={"X-Filename": "sample_resume_ai_consultant.txt"})

    assert response.status_code == 200
    body = response.json()
    assert body["parse_status"] == "parsed"
    assert body["created_profile"]["full_name"] == "Sam Patel"
