from __future__ import annotations

import pytest

from apps.backend.app.modules.document_generator.service import DocumentGeneratorService
from apps.backend.app.modules.fit_scoring.service import CandidateProfile, FitScoringService
from apps.backend.app.modules.job_discovery.service import Job, JobDiscoveryService
from apps.backend.app.modules.outreach_generator.service import OutreachGeneratorService
from apps.backend.app.modules.people_finder.service import PersonCandidate


def test_outreach_generator_creates_draft_for_verified_contact() -> None:
    profile = CandidateProfile(candidate_profile_id="profile-1", full_name="Sam Patel", primary_email="sam@example.com", location="India", timezone="Asia/Kolkata", target_roles=["AI Consultant"], approved_skills=["AI automation"])
    job = JobDiscoveryService.normalize(Job(source="greenhouse", source_url="https://example.com/jobs/genai", title="AI Consultant", company="Acme AI", remote=True, required_skills=["AI automation"]))
    score = FitScoringService().score(job, profile)
    package = DocumentGeneratorService().generate_package(job, profile, score)
    person = PersonCandidate(
        person_id="person-1",
        company="Acme AI",
        name="Jane Doe",
        title="Hiring Manager",
        person_type="likely_hiring_manager",
        source_url="https://example.com/team",
        source_type="company_page",
        email="jane.doe@example.com",
        email_verification_status="verified",
        confidence=0.9,
        why_relevant="Owns the team.",
    )

    draft = OutreachGeneratorService().generate(package, person)

    assert draft.status == "review_pending"
    assert draft.gmail_draft["to"] == "jane.doe@example.com"


def test_outreach_generator_blocks_unverified_or_linkedin_contacts() -> None:
    profile = CandidateProfile(candidate_profile_id="profile-1", full_name="Sam Patel", primary_email="sam@example.com", location="India", timezone="Asia/Kolkata")
    job = JobDiscoveryService.normalize(Job(source="greenhouse", source_url="https://example.com/jobs/genai", title="AI Consultant", company="Acme AI", remote=True))
    score = FitScoringService().score(job, profile)
    package = DocumentGeneratorService().generate_package(job, profile, score)
    blocked = PersonCandidate(
        person_id="person-2",
        company="Acme AI",
        name="Pat Doe",
        title="Recruiter",
        person_type="recruiter",
        source_url="https://linkedin.com/in/patdoe",
        source_type="linkedin",
        email="pat@example.com",
        email_verification_status="unverified",
        confidence=0.8,
        why_relevant="Recruiter",
    )

    with pytest.raises(ValueError):
        OutreachGeneratorService().generate(package, blocked)

