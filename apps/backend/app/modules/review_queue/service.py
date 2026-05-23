from __future__ import annotations

from dataclasses import asdict, dataclass

from apps.backend.app.modules.outreach_generator.service import OutreachDraft
from apps.backend.app.persistence_repos import ReviewItemRepository
from apps.backend.app.shared.contracts import ReviewQueueItem


@dataclass(frozen=True)
class ReviewItem:
    review_id: str
    user_id: str
    entity_type: str
    entity_id: str
    status: str
    requested_at: str
    reviewed_at: str | None = None
    review_notes: str | None = None


@dataclass(frozen=True)
class ReviewDecision:
    review_id: str
    decision: str
    notes: str | None


class ReviewQueueService:
    def __init__(self) -> None:
        self.repo = ReviewItemRepository()

    def create_review(self, user_id: str, entity_type: str, entity_id: str, requested_at: str) -> ReviewItem:
        review = ReviewItem(
            review_id=f"review-{entity_id}",
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            status="pending_review",
            requested_at=requested_at,
        )
        ReviewQueueItem.model_validate(asdict(review))
        self.repo.upsert(review.review_id, asdict(review))
        return review

    def approve(self, review: ReviewItem) -> ReviewDecision:
        if review.status != "pending_review":
            raise ValueError("review must be pending")
        return ReviewDecision(review.review_id, "approved", None)

    def set_status(self, review_id: str, status: str, notes: str | None = None) -> ReviewItem:
        payload = self.repo.get(review_id)
        if payload is None:
            raise KeyError(review_id)
        payload["status"] = status
        payload["review_notes"] = notes
        self.repo.upsert(review_id, payload)
        return ReviewItem(**payload)

    def list_all(self) -> list[ReviewItem]:
        return [ReviewItem(**item) for item in self.repo.list_all()]

    def gmail_draft_payload(self, draft: OutreachDraft) -> dict[str, str]:
        if draft.status != "review_pending":
            raise ValueError("draft must be pending review")
        if not draft.gmail_draft:
            raise ValueError("draft has no gmail payload")
        return draft.gmail_draft
