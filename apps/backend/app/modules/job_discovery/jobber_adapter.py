from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from apps.backend.app.config import settings

from .service import Job, JobSourceAdapter


@dataclass(frozen=True)
class JobberSource:
    board: str
    company_slug: str


def parse_jobber_sources(raw_sources: str) -> list[JobberSource]:
    sources: list[JobberSource] = []
    for item in raw_sources.split(","):
        value = item.strip()
        if not value or ":" not in value:
            continue
        board, company_slug = value.split(":", 1)
        board = board.strip().lower()
        company_slug = company_slug.strip()
        if board and company_slug:
            sources.append(JobberSource(board=board, company_slug=company_slug))
    return sources


class JobberATSAdapter(JobSourceAdapter):
    def __init__(
        self,
        sources: list[JobberSource] | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 10,
    ) -> None:
        self.sources = sources if sources is not None else parse_jobber_sources(settings.jobber_sources)
        self.base_url = (base_url or settings.jobber_base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.errors: list[dict[str, str]] = []

    def discover(self) -> list[Job]:
        jobs: list[Job] = []
        self.errors = []
        for source in self.sources:
            try:
                jobs.extend(self._fetch_source(source))
            except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
                self.errors.append(
                    {
                        "source": f"{source.board}:{source.company_slug}",
                        "message": str(exc),
                    }
                )
        return jobs

    def _fetch_source(self, source: JobberSource) -> list[Job]:
        url = f"{self.base_url}/{quote(source.board)}/{quote(source.company_slug)}"
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "jobcopilot/1.0"})
        with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - configured public ATS endpoint
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"Unexpected jobber response for {source.board}:{source.company_slug}")
        jobs: list[Job] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            link = str(item.get("link") or "").strip()
            if not title or not link:
                continue
            location = str(item.get("location") or "").strip() or None
            jobs.append(
                Job(
                    source=f"jobber:{source.board}",
                    source_url=link,
                    title=title,
                    company=source.company_slug,
                    location=location,
                    remote=_is_remote(location),
                    description=f"Imported from jobber OSS adapter source {source.board}:{source.company_slug}.",
                )
            )
        return jobs


def _is_remote(location: str | None) -> bool:
    if not location:
        return False
    lowered = location.lower()
    return any(token in lowered for token in ("remote", "anywhere", "americas", "global", "worldwide"))
