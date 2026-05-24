from __future__ import annotations

from fastapi.testclient import TestClient

from apps.backend.app.main import app
from apps.backend.app.config import Settings
from apps.backend.app.modules.oss_integrations.service import list_oss_integrations


def test_oss_integrations_endpoint_reports_all_requested_tools() -> None:
    response = TestClient(app).get("/api/oss/integrations")

    assert response.status_code == 200
    payload = response.json()
    keys = {item["key"] for item in payload["integrations"]}

    assert {
        "jobber",
        "ever-jobs",
        "docling",
        "cv-matcher",
        "reactive-resume",
        "open-resume",
        "browser-use",
        "crawlee-python",
        "langgraph",
        "pydantic-ai",
        "langfuse",
    }.issubset(keys)


def test_oss_registry_marks_safe_active_and_blocked_integrations() -> None:
    registry = list_oss_integrations(
        Settings(
            jobber_sources="ashby:linear",
            openresume_enabled=True,
            browser_automation_enabled=True,
            langfuse_host="https://langfuse.example",
            langfuse_public_key="pk",
            langfuse_secret_key="sk",
        )
    )
    integrations = {item.key: item for item in registry.integrations}

    assert integrations["jobber"].classification == "active_adapter"
    assert integrations["jobber"].enabled is True
    assert integrations["docling"].classification == "active_dependency"
    assert integrations["docling"].enabled is True
    assert integrations["open-resume"].classification == "blocked_license"
    assert integrations["open-resume"].enabled is True
    assert integrations["langfuse"].enabled is True
    assert "LinkedIn scraping" in " ".join(integrations["browser-use"].safety_notes)
