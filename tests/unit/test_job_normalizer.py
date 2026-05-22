from __future__ import annotations

from apps.backend.app.modules.job_discovery.service import Job, JobDiscoveryService


def test_job_normalizer_canonicalizes_url_and_removes_duplicates() -> None:
    jobs = [
        Job(source="greenhouse", source_url="https://example.com/jobs/1/", title="GenAI Engineer", company="Acme AI", required_skills=["FastAPI", "FastAPI"]),
        Job(source="lever", source_url="https://example.com/jobs/1", title="GenAI Engineer", company="Acme AI", required_skills=["FastAPI"]),
        Job(source="workday", source_url="https://example.com/jobs/2", title="Wrong Fit", company="Acme Finance"),
    ]

    normalized = JobDiscoveryService.normalize_and_dedup(jobs)

    assert len(normalized) == 2
    assert normalized[0].canonical_url == "https://example.com/jobs/1"
    assert normalized[0].required_skills == ["FastAPI"]

