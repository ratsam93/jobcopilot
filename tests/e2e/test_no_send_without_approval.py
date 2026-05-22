from __future__ import annotations

import pytest

from apps.backend.app.modules.document_generator.service import DocumentGeneratorService
from apps.backend.app.modules.fit_scoring.service import CandidateProfile, FitScoringService
from apps.backend.app.modules.job_discovery.service import Job, JobDiscoveryService
from apps.backend.app.modules.outreach_generator.service import OutreachGeneratorService
from apps.backend.app.modules.people_finder.service import PersonCandidate
from apps.backend.app.modules.review_queue.service import ReviewQueueService


def test_no_send_without_approval() -> None:
    profile = CandidateProfile(candidate_profile_id="profile-1", full_name="Sam Patel", primary_email="sam@example.com", location="India", timezone="Asia/Kolkata", target_roles=["AI Consultant"], approved_skills=["AI automation"])
    job = JobDiscoveryService.normalize(Job(source="greenhouse", source_url="https://example.com/jobs/genai", title="AI Consultant", company="Acme AI", remote=True))
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
    review = ReviewQueueService().create_review("user-1", "outreach_draft", draft.outreach_draft_id, "2026-05-21T00:00:00Z")

    assert review.status == "pending_review"
    with pytest.raises(ValueError):
        ReviewQueueService().gmail_draft_payload(type("Draft", (), {"status": "drafted", "gmail_draft": {"to": "jane.doe@example.com"}})())

