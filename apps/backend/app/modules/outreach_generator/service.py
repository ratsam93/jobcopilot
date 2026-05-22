from __future__ import annotations

from dataclasses import dataclass, field

from apps.backend.app.modules.document_generator.service import ApplicationPackage
from apps.backend.app.modules.people_finder.service import PersonCandidate


@dataclass(frozen=True)
class OutreachDraft:
    outreach_draft_id: str
    application_package_id: str
    person_id: str
    channel: str
    draft_type: str
    subject: str
    body: str
    personalization_points: list[str] = field(default_factory=list)
    status: str = "review_pending"
    gmail_draft: dict[str, str] | None = None


class OutreachGeneratorService:
    def __init__(self) -> None:
        self.drafts: dict[str, OutreachDraft] = {}

    def generate(self, package: ApplicationPackage, person: PersonCandidate) -> OutreachDraft:
        if person.do_not_contact:
            raise ValueError("person is do-not-contact")
        if "linkedin.com" in person.source_url.lower() or person.source_type.lower() == "linkedin":
            raise ValueError("linkedin outreach is blocked")
        if person.email_verification_status != "verified":
            raise ValueError("recipient email is unverified")
        subject = f"Application for {package.job_id}"
        body = (
            f"Hi {person.name},\n\n"
            f"I’m reaching out about the role tied to {package.job_id}. "
            f"The fit is strongest on {', '.join(package.fit_summary[:2])}.\n"
        )
        draft = OutreachDraft(
            outreach_draft_id=f"draft-{package.application_package_id}-{person.person_id}",
            application_package_id=package.application_package_id,
            person_id=person.person_id,
            channel="email",
            draft_type="hiring_manager_email",
            subject=subject,
            body=body,
            personalization_points=package.fit_summary[:2],
            gmail_draft={
                "to": person.email or "",
                "subject": subject,
                "body": body,
            },
        )
        self.drafts[draft.outreach_draft_id] = draft
        return draft

    def get(self, outreach_draft_id: str) -> OutreachDraft:
        return self.drafts[outreach_draft_id]
