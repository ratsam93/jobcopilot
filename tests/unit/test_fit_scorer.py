from __future__ import annotations

from apps.backend.app.modules.fit_scoring.service import CandidateProfile, FitScoringService
from apps.backend.app.modules.job_discovery.service import Job, JobDiscoveryService


def test_fit_scorer_separates_strong_and_weak_fits() -> None:
    scorer = FitScoringService()
    profile = CandidateProfile(
        candidate_profile_id="profile-1",
        full_name="Sam Patel",
        primary_email="sam@example.com",
        location="India",
        timezone="Asia/Kolkata",
        target_roles=["GenAI Engineer", "AI Consultant"],
        approved_skills=["AI automation", "FastAPI", "LLMs"],
    )

    strong = scorer.score(
        JobDiscoveryService.normalize(Job(source="greenhouse", source_url="https://example.com/jobs/genai", title="GenAI Engineer", company="Acme AI", remote=True, required_skills=["AI automation", "FastAPI"])),
        profile,
    )
    weak = scorer.score(
        JobDiscoveryService.normalize(Job(source="workday", source_url="https://example.com/jobs/accountant", title="Senior Accountant", company="Acme Finance", remote=False, required_skills=["Excel", "GAAP"])),
        profile,
    )

    assert strong.decision == "generate_application_package"
    assert strong.fit_score >= 85
    assert weak.decision == "reject"
    assert weak.fit_score < strong.fit_score

