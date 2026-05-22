from __future__ import annotations

import pytest

from apps.backend.app.modules.review_queue.service import ReviewQueueService


def test_review_queue_blocks_without_approval() -> None:
    service = ReviewQueueService()
    review = service.create_review("user-1", "outreach_draft", "draft-1", "2026-05-21T00:00:00Z")

    decision = service.approve(review)

    assert decision.decision == "approved"
    with pytest.raises(ValueError):
        service.gmail_draft_payload(type("Draft", (), {"status": "drafted", "gmail_draft": {"to": "sam@example.com"}})())

