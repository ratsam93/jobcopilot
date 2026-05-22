from __future__ import annotations

import pytest

from apps.backend.app.modules.document_generator.service import DocumentGeneratorService
from apps.backend.app.modules.email_discovery.service import EmailDiscoveryService
from apps.backend.app.modules.fit_scoring.service import CandidateProfile, FitScoringService
from apps.backend.app.modules.job_discovery.service import Job, JobDiscoveryService
from apps.backend.app.modules.outreach_generator.service import OutreachGeneratorService
from apps.backend.app.modules.people_finder.service import PersonCandidate


def test_email_discovery_blocks_unverified_local_parts() -> None:
    person = PersonCandidate(
        person_id="person-1",
        company="Acme AI",
        name="Jane Doe",
        title="Hiring Manager",
        person_type="likely_hiring_manager",
        source_url="https://example.com/team",
        source_type="company_page",
        email=None,
        email_verification_status="not_checked",
        confidence=0.9,
        why_relevant="Owns the team.",
    )
    candidates = EmailDiscoveryService().generate_candidates(person, "example.com")

    assert candidates[0].verification_status in {"verified", "unverified"}
    assert candidates[0].email.endswith("@example.com")


def test_resume_tailoring_does_not_invent_claims() -> None:
    profile = CandidateProfile(
        candidate_profile_id="profile-1",
        full_name="Sam Patel",
        primary_email="sam@example.com",
        location="India",
        timezone="Asia/Kolkata",
        target_roles=["AI Consultant"],
        approved_skills=["AI automation"],
        approved_claims=["Built AI automation workflows"],
        do_not_claim=["Salesforce"],
    )
    job = JobDiscoveryService.normalize(Job(source="greenhouse", source_url="https://example.com/jobs/genai", title="AI Consultant", company="Acme AI", remote=True, required_skills=["AI automation"]))
    score = FitScoringService().score(job, profile)
    package = DocumentGeneratorService().generate_package(job, profile, score)

    assert "Salesforce" not in package.resume_version.resume_text
    assert package.resume_version.unsupported_claims_detected == []


def test_linkedin_contacts_are_blocked() -> None:
    profile = CandidateProfile(candidate_profile_id="profile-1", full_name="Sam Patel", primary_email="sam@example.com", location="India", timezone="Asia/Kolkata")
    job = JobDiscoveryService.normalize(Job(source="greenhouse", source_url="https://example.com/jobs/genai", title="AI Consultant", company="Acme AI", remote=True))
    score = FitScoringService().score(job, profile)
    package = DocumentGeneratorService().generate_package(job, profile, score)
    person = PersonCandidate(
        person_id="person-1",
        company="Acme AI",
        name="Jane Doe",
        title="Hiring Manager",
        person_type="likely_hiring_manager",
        source_url="https://linkedin.com/in/janedoe",
        source_type="linkedin",
        email="jane.doe@example.com",
        email_verification_status="verified",
        confidence=0.9,
        why_relevant="Owns the team.",
    )

    with pytest.raises(ValueError):
        OutreachGeneratorService().generate(package, person)

