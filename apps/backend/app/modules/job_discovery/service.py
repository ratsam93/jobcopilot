from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Protocol
from urllib.parse import urlparse

from apps.backend.app.persistence_repos import JobRecordRepository
from apps.backend.app.shared.contracts import JobParseResult


@dataclass(frozen=True)
class Job:
    source: str
    source_url: str
    title: str
    company: str
    location: str | None = None
    remote: bool = False
    description: str = ""
    salary_min_usd: int | None = None
    salary_max_usd: int | None = None
    required_skills: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class NormalizedJob:
    job_id: str
    title: str
    company: str
    source: str
    source_url: str
    canonical_url: str
    location: str | None
    remote: bool
    description: str
    salary_min_usd: int | None
    salary_max_usd: int | None
    required_skills: list[str]
    dedup_key: str


class JobSourceAdapter(Protocol):
    def discover(self) -> list[Job]:
        raise NotImplementedError


@dataclass(frozen=True)
class JobRecord:
    normalized_job: NormalizedJob
    persisted_at: str
    discovery_batch_id: str


class JobDiscoveryStore:
    def __init__(self) -> None:
        self.repo = JobRecordRepository()

    def persist(self, jobs: list[NormalizedJob], discovery_batch_id: str = "batch-1", persisted_at: str = "2026-05-21T00:00:00Z") -> list[JobRecord]:
        persisted: list[JobRecord] = []
        for job in jobs:
            record = JobRecord(normalized_job=job, persisted_at=persisted_at, discovery_batch_id=discovery_batch_id)
            self.repo.upsert(
                job.job_id,
                {
                    "normalized_job_json": asdict(job),
                    "persisted_at": persisted_at,
                    "discovery_batch_id": discovery_batch_id,
                },
                persisted_at=persisted_at,
                discovery_batch_id=discovery_batch_id,
            )
            JobParseResult.model_validate(asdict(job))
            persisted.append(record)
        return persisted

    def list(self) -> list[NormalizedJob]:
        return [NormalizedJob(**item["normalized_job_json"]) for item in self.repo.list_all()]

    def get(self, job_id: str) -> JobRecord:
        payload = self.repo.get(job_id)
        if payload is None:
            raise KeyError(job_id)
        return JobRecord(
            normalized_job=NormalizedJob(**payload["normalized_job_json"]),
            persisted_at=payload["persisted_at"],
            discovery_batch_id=payload["discovery_batch_id"],
        )


class JobDiscoveryService:
    def __init__(self, adapters: list[JobSourceAdapter] | None = None, store: JobDiscoveryStore | None = None) -> None:
        self.adapters = adapters or []
        self.store = store or JobDiscoveryStore()

    def discover(self) -> list[Job]:
        jobs: list[Job] = []
        for adapter in self.adapters:
            jobs.extend(adapter.discover())
        return jobs

    def discover_and_persist(self) -> list[JobRecord]:
        normalized = self.normalize_and_dedup(self.discover())
        return self.store.persist(normalized)

    @staticmethod
    def normalize(job: Job) -> NormalizedJob:
        canonical_url = _canonicalize_url(job.source_url)
        dedup_key = _dedup_key(job.company, job.title, canonical_url)
        return NormalizedJob(
            job_id=dedup_key,
            title=job.title.strip(),
            company=job.company.strip(),
            source=job.source.strip(),
            source_url=job.source_url.strip(),
            canonical_url=canonical_url,
            location=job.location.strip() if job.location else None,
            remote=bool(job.remote),
            description=job.description.strip(),
            salary_min_usd=job.salary_min_usd,
            salary_max_usd=job.salary_max_usd,
            required_skills=_dedupe_preserve_order(job.required_skills),
            dedup_key=dedup_key,
        )

    @classmethod
    def normalize_and_dedup(cls, jobs: list[Job]) -> list[NormalizedJob]:
        seen: set[str] = set()
        normalized: list[NormalizedJob] = []
        for job in jobs:
            item = cls.normalize(job)
            if item.dedup_key in seen:
                continue
            seen.add(item.dedup_key)
            normalized.append(item)
        return normalized


def _canonicalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}".lower()


def _dedup_key(company: str, title: str, canonical_url: str) -> str:
    raw = f"{company.strip().lower()}|{title.strip().lower()}|{canonical_url}"
    return sha256(raw.encode("utf-8")).hexdigest()[:16]


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        key = value.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(value.strip())
    return output
