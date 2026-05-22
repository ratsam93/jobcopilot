from apps.backend.app.modules.document_generator.service import DocumentGeneratorService
from apps.backend.app.modules.email_discovery.service import EmailDiscoveryService
from apps.backend.app.modules.fit_scoring.service import CandidateProfile, FitScoringService
from apps.backend.app.modules.job_discovery.service import Job, JobDiscoveryService
from apps.backend.app.modules.outreach_generator.service import OutreachGeneratorService
from apps.backend.app.modules.people_finder.service import PersonCandidate, PeopleFinderService
from apps.backend.app.modules.review_queue.service import ReviewQueueService
from apps.backend.app.modules.tracker.service import TrackerService


def test_discovery_normalization_dedups_jobs():
    jobs = [
        Job(source="source-a", source_url="https://example.com/jobs/1/", title="AI Consultant", company="Acme", required_skills=["AI", "SQL"]),
        Job(source="source-b", source_url="https://example.com/jobs/1", title="AI Consultant", company="Acme", required_skills=["AI"]),
    ]
    normalized = JobDiscoveryService.normalize_and_dedup(jobs)
    assert len(normalized) == 1
    assert normalized[0].canonical_url == "https://example.com/jobs/1"


def test_scoring_package_outreach_review_and_tracker_flow():
    job = JobDiscoveryService.normalize(Job(source="source-a", source_url="https://example.com/jobs/2", title="AI Consultant", company="Acme", remote=True, required_skills=["AI automation", "Consulting"]))
    profile = CandidateProfile(
        candidate_profile_id="profile-1",
        full_name="Sam",
        primary_email="sam@example.com",
        location="India",
        timezone="Asia/Kolkata",
        target_roles=["AI Consultant"],
        target_geographies=["Remote"],
        salary_min_usd=30000,
        remote_preference="required",
        approved_skills=["AI automation", "Consulting"],
        approved_claims=["Built AI automation"],
        do_not_claim=["Salesforce"],
    )

    score = FitScoringService().score(job, profile)
    assert score.decision == "generate_application_package"
    assert score.fit_score >= 85

    package = DocumentGeneratorService().generate_package(job, profile, score)
    assert package.status == "review_pending"
    assert package.resume_version.unsupported_claims_detected == []

    person = PersonCandidate(
        person_id="person-1",
        company="Acme",
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

    found_people = PeopleFinderService().find_people(package)
    assert len(found_people) == 2

    email_candidates = EmailDiscoveryService().generate_candidates(person, "example.com")
    assert email_candidates[0].verification_status == "verified"

    outreach = OutreachGeneratorService().generate(package, person)
    assert outreach.status == "review_pending"
    assert outreach.gmail_draft["to"] == "jane.doe@example.com"

    review = ReviewQueueService().create_review("user-1", "outreach_draft", outreach.outreach_draft_id, "2026-05-21T00:00:00Z")
    decision = ReviewQueueService().approve(review)
    assert decision.decision == "approved"
    assert ReviewQueueService().gmail_draft_payload(outreach)["subject"] == outreach.subject

    tracker = TrackerService().create_for_job(job.job_id, "campaign-1", profile.candidate_profile_id)
    tracker = TrackerService().record_event(tracker, "outreach_draft_created", "Hiring manager draft created", "2026-05-21T00:00:00Z")
    tracker = TrackerService().schedule_followup(tracker, "2026-05-28T00:00:00Z", "email", "First follow-up")
    assert tracker.status == "followup_due"
    assert len(tracker.events) == 1
    assert len(tracker.followups) == 1


def test_outreach_blocks_unverified_or_dnc_recipients():
    service = OutreachGeneratorService()
    job = JobDiscoveryService.normalize(Job(source="source-a", source_url="https://example.com/jobs/3", title="AI Consultant", company="Acme", remote=True))
    profile = CandidateProfile(candidate_profile_id="profile-1", full_name="Sam", primary_email="sam@example.com", location="India", timezone="Asia/Kolkata")
    score = FitScoringService().score(job, profile)
    package = DocumentGeneratorService().generate_package(job, profile, score)
    unverified_person = PersonCandidate(
        person_id="person-2",
        company="Acme",
        name="Pat Doe",
        title="Recruiter",
        person_type="recruiter",
        source_url="https://example.com/team",
        source_type="company_page",
        email="pat@example.com",
        email_verification_status="unverified",
        confidence=0.7,
        why_relevant="Recruiter",
    )
    try:
        service.generate(package, unverified_person)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "unverified" in str(exc)


def test_job_discovery_persists_normalized_results():
    class Adapter:
        def discover(self):
            return [
                Job(source="adapter-a", source_url="https://example.com/jobs/4/", title="ML Engineer", company="Beta", required_skills=["Python"]),
                Job(source="adapter-b", source_url="https://example.com/jobs/4", title="ML Engineer", company="Beta", required_skills=["Python"]),
            ]

    service = JobDiscoveryService(adapters=[Adapter()])
    records = service.discover_and_persist()
    assert len(records) == 1
    assert service.store.get(records[0].normalized_job.job_id).normalized_job.title == "ML Engineer"


def test_review_requires_pending_status_and_outreach_blocks_linkedin():
    job = JobDiscoveryService.normalize(Job(source="source-a", source_url="https://example.com/jobs/5", title="Backend Engineer", company="Acme", remote=True))
    profile = CandidateProfile(candidate_profile_id="profile-1", full_name="Sam", primary_email="sam@example.com", location="India", timezone="Asia/Kolkata")
    score = FitScoringService().score(job, profile)
    package = DocumentGeneratorService().generate_package(job, profile, score)
    person = PersonCandidate(
        person_id="person-linkedin",
        company="Acme",
        name="Alex Doe",
        title="Recruiter",
        person_type="recruiter",
        source_url="https://linkedin.com/in/alex",
        source_type="linkedin",
        email="alex@example.com",
        email_verification_status="verified",
        confidence=0.9,
        why_relevant="Recruiter",
    )
    try:
        OutreachGeneratorService().generate(package, person)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "linkedin" in str(exc)

    review_service = ReviewQueueService()
    review = review_service.create_review("user-1", "outreach_draft", "draft-1", "2026-05-21T00:00:00Z")
    review_service.approve(review)
    try:
        review_service.approve(review.__class__(**{**review.__dict__, "status": "approved"}))
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "pending" in str(exc)
