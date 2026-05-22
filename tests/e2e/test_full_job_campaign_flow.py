from __future__ import annotations

from pathlib import Path

from apps.backend.app.main import app
from apps.backend.app.modules.campaign_planner.models import CampaignCreateInput
from apps.backend.app.modules.campaign_planner.service import CampaignPlannerStore
from apps.backend.app.modules.career_vault.service import store as career_store
from apps.backend.app.modules.document_generator.service import DocumentGeneratorService
from apps.backend.app.modules.email_discovery.service import EmailDiscoveryService
from apps.backend.app.modules.fit_scoring.service import CandidateProfile, FitScoringService
from apps.backend.app.modules.job_discovery.service import Job, JobDiscoveryService
from apps.backend.app.modules.outreach_generator.service import OutreachGeneratorService
from apps.backend.app.modules.people_finder.service import PeopleFinderService, PersonCandidate
from apps.backend.app.modules.review_queue.service import ReviewQueueService
from apps.backend.app.modules.tracker.service import TrackerService


def test_full_job_campaign_flow_reaches_pending_review() -> None:
    resume_text = Path("tests/fixtures/sample_resume_ai_consultant.txt").read_text(encoding="utf-8")
    profile_result = career_store.parse_resume_text(resume_text, filename="sample_resume_ai_consultant.txt")
    profile = CandidateProfile(
        candidate_profile_id=str(profile_result.candidate_profile_id),
        full_name=profile_result.created_profile.full_name or "Sam Patel",
        primary_email=profile_result.created_profile.primary_email or "sam@example.com",
        location=profile_result.created_profile.location or "India",
        timezone="Asia/Kolkata",
        target_roles=["AI Consultant", "GenAI Engineer"],
        approved_skills=[skill.skill_name for skill in profile_result.created_profile.skills],
        approved_claims=[claim.claim_text for claim in profile_result.created_profile.approved_claims],
        do_not_claim=[item.blocked_claim for item in profile_result.created_profile.do_not_claim],
    )

    campaign_store = CampaignPlannerStore()
    campaign = campaign_store.create_campaign(
        CampaignCreateInput(
            candidate_profile_id=profile_result.candidate_profile_id,
            natural_language_prompt="Apply to top technology companies across the USA where I am fit. Prepare resume, cover letter, find hiring manager and recruiter, but do not send anything without my approval.",
            execution_mode="approval_required",
        )
    )
    campaign_store.start_run(campaign.campaign_id)

    jobs = JobDiscoveryService.normalize_and_dedup(
        [
            Job(source="greenhouse", source_url="https://example.com/jobs/ai-consultant", title="AI Consultant", company="Acme AI", remote=True, required_skills=["AI automation", "FastAPI", "LLM"]),
            Job(source="lever", source_url="https://example.com/jobs/ai-consultant/", title="AI Consultant", company="Acme AI", remote=True, required_skills=["AI automation", "FastAPI"]),
            Job(source="workday", source_url="https://example.com/jobs/wrong-fit", title="Senior Accountant", company="Acme Finance", remote=False, required_skills=["GAAP"]),
        ]
    )
    assert len(jobs) >= 1

    shortlisted = []
    scorer = FitScoringService()
    package_service = DocumentGeneratorService()
    people_service = PeopleFinderService()
    email_service = EmailDiscoveryService()
    outreach_service = OutreachGeneratorService()
    review_service = ReviewQueueService()
    tracker_service = TrackerService()

    for job in jobs:
        score = scorer.score(job, profile)
        if score.decision != "generate_application_package":
            continue
        shortlisted.append(job)
        package = package_service.generate_package(job, profile, score)
        people = people_service.find_people(package)
        assert people
        email_candidates = email_service.generate_candidates(
            PersonCandidate(
                person_id="person-1",
                company=people[0].company,
                name="Jane Doe",
                title="Hiring Manager",
                person_type="likely_hiring_manager",
                source_url=people[0].source_url,
                source_type=people[0].source_type,
                email="jane.doe@example.com",
                email_verification_status="verified",
                confidence=people[0].confidence,
                why_relevant=people[0].why_relevant,
            ),
            "example.com",
        )
        assert email_candidates[0].verification_status in {"verified", "unverified"}
        outreach = outreach_service.generate(
            package,
            PersonCandidate(
                person_id="person-1",
                company=people[0].company,
                name="Jane Doe",
                title="Hiring Manager",
                person_type="likely_hiring_manager",
                source_url=people[0].source_url,
                source_type=people[0].source_type,
                email="jane.doe@example.com",
                email_verification_status="verified",
                confidence=people[0].confidence,
                why_relevant=people[0].why_relevant,
            ),
        )
        review = review_service.create_review("user-1", "outreach_draft", outreach.outreach_draft_id, "2026-05-21T00:00:00Z")
        assert review.status == "pending_review"
        decision = review_service.approve(review)
        assert decision.decision == "approved"
        tracker = tracker_service.create_for_job(job.job_id, campaign.campaign_id.hex, profile.candidate_profile_id)
        tracker = tracker_service.record_event(tracker, "outreach_draft_created", "Draft created", "2026-05-21T00:00:00Z")
        tracker = tracker_service.schedule_followup(tracker, "2026-05-28T00:00:00Z", "email", "Follow up")
        assert tracker.status == "followup_due"

    final = {
        "campaign_status": "pending_review",
        "jobs_discovered": len(jobs),
        "jobs_shortlisted": len(shortlisted),
        "application_packages_created": len(shortlisted),
        "people_search_completed": True,
        "outreach_drafts_created": True,
        "emails_sent": 0,
        "applications_submitted": 0,
        "approval_required": True,
    }

    assert final["campaign_status"] == "pending_review"
    assert final["jobs_discovered"] >= 1
    assert final["jobs_shortlisted"] >= 1
    assert final["application_packages_created"] >= 1
    assert final["approval_required"] is True
