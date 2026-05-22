from __future__ import annotations

from apps.backend.app.modules.document_generator.service import DocumentGeneratorService
from apps.backend.app.modules.fit_scoring.service import CandidateProfile, FitScoringService
from apps.backend.app.modules.job_discovery.service import Job, JobDiscoveryService
from apps.backend.app.modules.people_finder.service import PeopleFinderService


def test_people_ranker_returns_source_and_confidence() -> None:
    profile = CandidateProfile(candidate_profile_id="profile-1", full_name="Sam Patel", primary_email="sam@example.com", location="India", timezone="Asia/Kolkata", target_roles=["AI Consultant"], approved_skills=["AI automation"])
    job = JobDiscoveryService.normalize(Job(source="greenhouse", source_url="https://example.com/jobs/genai", title="AI Consultant", company="Acme AI", remote=True, required_skills=["AI automation"]))
    score = FitScoringService().score(job, profile)
    package = DocumentGeneratorService().generate_package(job, profile, score)

    people = PeopleFinderService().find_people(package)

    assert len(people) == 2
    assert all(person.source_url for person in people)
    assert all(person.confidence > 0 for person in people)

