from __future__ import annotations

from dataclasses import asdict, dataclass

from apps.backend.app.modules.document_generator.service import ApplicationPackage
from apps.backend.app.persistence_repos import PeopleCacheRepository


@dataclass(frozen=True)
class PersonCandidate:
    person_id: str
    company: str
    name: str
    title: str
    person_type: str
    source_url: str
    source_type: str
    email: str | None
    email_verification_status: str
    confidence: float
    why_relevant: str
    do_not_contact: bool = False


@dataclass(frozen=True)
class EmailCandidate:
    email_candidate_id: str
    person_id: str
    email: str
    generation_method: str
    source_domain: str
    verification_status: str
    verification_score: float
    verified_at: str | None


class PeopleFinderService:
    def __init__(self) -> None:
        self.repo = PeopleCacheRepository()

    def find_people(self, package: ApplicationPackage) -> list[PersonCandidate]:
        if package.status != "review_pending":
            return []
        people = [
            PersonCandidate(
                person_id=f"person-{package.job_id}-hm",
                company=package.job_id,
                name="Hiring Manager",
                title="Hiring Manager",
                person_type="likely_hiring_manager",
                source_url="https://company.example/team",
                source_type="company_page",
                email=None,
                email_verification_status="not_checked",
                confidence=0.78,
                why_relevant="Likely owns the role or team.",
            ),
            PersonCandidate(
                person_id=f"person-{package.job_id}-rec",
                company=package.job_id,
                name="Recruiter",
                title="Talent Partner",
                person_type="recruiter",
                source_url="https://company.example/careers",
                source_type="public_web",
                email=None,
                email_verification_status="not_checked",
                confidence=0.74,
                why_relevant="Likely handles hiring for this role.",
            ),
        ]
        ranked = sorted(people, key=lambda item: item.confidence, reverse=True)
        self.repo.upsert(package.application_package_id, {"people": [asdict(person) for person in ranked]})
        return ranked

    def get_cached(self, application_package_id: str) -> list[PersonCandidate]:
        payload = self.repo.get(application_package_id)
        if payload is None:
            return []
        return [PersonCandidate(**item) for item in payload["people"]]
