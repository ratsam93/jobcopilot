from __future__ import annotations

from apps.backend.app.modules.job_discovery.service import Job, JobDiscoveryService, JobDiscoveryStore


def test_job_discovery_normalizes_and_persists_jobs() -> None:
    store = JobDiscoveryStore()
    service = JobDiscoveryService(store=store)
    records = service.store.persist(
        JobDiscoveryService.normalize_and_dedup(
            [
                Job(source="greenhouse", source_url="https://example.com/jobs/1/", title="GenAI Engineer", company="Acme AI", remote=True),
                Job(source="lever", source_url="https://example.com/jobs/1", title="GenAI Engineer", company="Acme AI", remote=True),
            ]
        )
    )

    assert len(records) == 1
    assert service.store.list()[0].title == "GenAI Engineer"

