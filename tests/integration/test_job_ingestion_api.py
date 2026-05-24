from __future__ import annotations

from apps.backend.app.modules.job_discovery.service import Job, JobDiscoveryService, JobDiscoveryStore
from apps.backend.app.modules.job_discovery.jobber_adapter import JobberATSAdapter, JobberSource, parse_jobber_sources


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


def test_jobber_source_config_parser() -> None:
    sources = parse_jobber_sources("ashby:linear, lever:netlify, bad-entry, greenhouse:airbnb")

    assert sources == [
        JobberSource(board="ashby", company_slug="linear"),
        JobberSource(board="lever", company_slug="netlify"),
        JobberSource(board="greenhouse", company_slug="airbnb"),
    ]


def test_jobber_adapter_maps_oss_response_to_jobs(monkeypatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self) -> bytes:
            return b'[{"title":"AI Engineer","location":"Remote","link":"https://jobs.example.com/1"}]'

    def fake_urlopen(request, timeout):
        assert request.full_url == "https://jobber.local/ashby/linear"
        assert timeout == 10
        return FakeResponse()

    monkeypatch.setattr("apps.backend.app.modules.job_discovery.jobber_adapter.urlopen", fake_urlopen)

    jobs = JobberATSAdapter(
        sources=[JobberSource(board="ashby", company_slug="linear")],
        base_url="https://jobber.local",
    ).discover()

    assert len(jobs) == 1
    assert jobs[0].source == "jobber:ashby"
    assert jobs[0].company == "linear"
    assert jobs[0].title == "AI Engineer"
    assert jobs[0].remote is True
