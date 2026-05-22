# Job Copilot Backend Test Plan

## Scope

Validate the backend against the SRS and SRS 2.0 addendum using pytest and FastAPI `TestClient`.

## Layers

- Unit tests for parsers, scoring, tailoring, ranking, outreach, and compliance guards.
- Integration tests for API endpoints and module handoff behavior.
- End-to-end tests for the full campaign flow and safety gates.

## Pass Criteria

- Health endpoint responds.
- Resume upload creates or reuses a Career Vault profile.
- Campaign parsing produces structured data.
- Job normalization removes duplicates.
- Fit scoring differentiates strong and weak fits.
- Resume tailoring uses only approved claims.
- People results contain source URL and confidence.
- Unverified email addresses are blocked.
- Review gating prevents sending without approval.
- LinkedIn automation is blocked.
- Full campaign flow stops at `pending_review`.

