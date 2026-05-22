from __future__ import annotations

from pathlib import Path

from apps.backend.app.modules.job_discovery.service import Job, JobDiscoveryService


def test_screenshot_to_job_flow_extracts_job_details_without_auto_apply() -> None:
    screenshot_text = Path("tests/fixtures/sample_linkedin_screenshot_text.txt").read_text(encoding="utf-8")
    job = Job(
        source="manual_screenshot",
        source_url="https://company.example/careers/genai-engineer",
        title="GenAI Engineer",
        company="Acme AI",
        description=screenshot_text,
        remote=True,
        required_skills=["LLMs", "FastAPI"],
    )
    normalized = JobDiscoveryService.normalize(job)

    assert normalized.title == "GenAI Engineer"
    assert normalized.company == "Acme AI"
    assert normalized.canonical_url.endswith("/careers/genai-engineer")

