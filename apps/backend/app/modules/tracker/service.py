from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TrackerApplication:
    application_id: str
    job_id: str
    campaign_id: str
    candidate_profile_id: str
    status: str = "found"
    notes: str = ""
    next_followup_at: str | None = None
    events: list["TrackerEvent"] = field(default_factory=list)
    followups: list["TrackerFollowup"] = field(default_factory=list)


@dataclass(frozen=True)
class TrackerEvent:
    event_id: str
    application_id: str
    event_type: str
    notes: str
    metadata_json: dict[str, str]
    created_at: str


@dataclass(frozen=True)
class TrackerFollowup:
    followup_id: str
    application_id: str
    due_date: str
    followup_type: str
    status: str
    notes: str


class TrackerService:
    def __init__(self) -> None:
        self.applications: dict[str, TrackerApplication] = {}

    def create_for_job(self, job_id: str, campaign_id: str, candidate_profile_id: str) -> TrackerApplication:
        application = TrackerApplication(
            application_id=f"app-{job_id}",
            job_id=job_id,
            campaign_id=campaign_id,
            candidate_profile_id=candidate_profile_id,
        )
        self.applications[application.application_id] = application
        return application

    def record_event(self, application: TrackerApplication, event_type: str, notes: str, created_at: str) -> TrackerApplication:
        event = TrackerEvent(
            event_id=f"event-{application.application_id}-{len(application.events) + 1}",
            application_id=application.application_id,
            event_type=event_type,
            notes=notes,
            metadata_json={},
            created_at=created_at,
        )
        updated = TrackerApplication(
            application_id=application.application_id,
            job_id=application.job_id,
            campaign_id=application.campaign_id,
            candidate_profile_id=application.candidate_profile_id,
            status=application.status,
            notes=application.notes,
            next_followup_at=application.next_followup_at,
            events=[*application.events, event],
            followups=application.followups,
        )
        self.applications[updated.application_id] = updated
        return updated

    def schedule_followup(self, application: TrackerApplication, due_date: str, followup_type: str, notes: str) -> TrackerApplication:
        followup = TrackerFollowup(
            followup_id=f"followup-{application.application_id}-{len(application.followups) + 1}",
            application_id=application.application_id,
            due_date=due_date,
            followup_type=followup_type,
            status="due",
            notes=notes,
        )
        updated = TrackerApplication(
            application_id=application.application_id,
            job_id=application.job_id,
            campaign_id=application.campaign_id,
            candidate_profile_id=application.candidate_profile_id,
            status="followup_due",
            notes=application.notes,
            next_followup_at=due_date,
            events=application.events,
            followups=[*application.followups, followup],
        )
        self.applications[updated.application_id] = updated
        return updated

    def get(self, application_id: str) -> TrackerApplication:
        return self.applications[application_id]
