from __future__ import annotations

from apps.backend.app.modules.document_generator.service import DocumentGeneratorService
from apps.backend.app.modules.fit_scoring.service import CandidateProfile, FitScoringService
from apps.backend.app.modules.job_discovery.service import Job, JobDiscoveryService


def test_resume_tailor_uses_only_approved_claims_and_creates_change_log() -> None:
    profile = CandidateProfile(
        candidate_profile_id="profile-1",
        full_name="Sam Patel",
        primary_email="sam@example.com",
        location="India",
        timezone="Asia/Kolkata",
        target_roles=["AI Consultant"],
        approved_skills=["AI automation", "FastAPI"],
        approved_claims=["Built AI automation workflows"],
        do_not_claim=["Salesforce"],
    )
    job = JobDiscoveryService.normalize(
        Job(source="greenhouse", source_url="https://example.com/jobs/genai", title="AI Consultant", company="Acme AI", remote=True, required_skills=["AI automation", "FastAPI"])
    )
    score = FitScoringService().score(job, profile)
    package = DocumentGeneratorService().generate_package(job, profile, score)

    assert "Sam Patel" in package.resume_version.resume_text
    assert package.resume_version.change_log
    assert package.unsupported_claims_detected == []
    assert "Acme AI" in package.cover_letter

