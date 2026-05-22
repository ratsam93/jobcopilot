# Job Copilot Backend Plan

## Purpose

Build a backend-first modular monolith for AI-assisted job search, campaign planning, job discovery, fit scoring, application package generation, outreach drafting, review, and tracking.

## Non-Negotiable Constraints

- Backend only for MVP.
- FastAPI API-first implementation.
- PostgreSQL for relational state.
- Qdrant for semantic search.
- Background workers for long-running flows.
- Gmail draft creation only; no automatic sending.
- No LinkedIn scraping or automation.
- Human approval required before final external action.
- All AI outputs must be schema-validated.
- All module boundaries must remain explicit.

## Architecture

### Core shape

- `core_kernel` owns orchestration, audit, permissions, and event routing.
- `modules/*` owns domain-specific behavior.
- `shared/*` owns contracts, schemas, prompts, observability helpers, and utilities.

### Initial module set

- P0 Core Orchestration Kernel
- P1 Career Vault
- P2 Campaign Planner
- P3 Job Discovery
- P4 Fit Scoring
- P5 Document Generator
- P6 People Finder
- P7 Outreach Generator
- P8 Review Queue
- P9 Tracker
- P10 Email Discovery
- P11 Autonomous Browsing

## Suggested Repository Shape

```text
jobcopilot/
  apps/backend/app/
  apps/backend/migrations/
  docs/
  packages/
  specs/job-copilot-backend/
```

## Delivery Strategy

1. Bootstrap project skeleton and local development plumbing.
2. Implement core kernel and persistence.
3. Add career vault and campaign planning.
4. Add discovery, scoring, package generation, and people/outreach flows.
5. Add review queue, Gmail draft integration, and tracker.
6. Add tests and harden safety/compliance behavior.

## Repository Strategy

- Keep production code in `apps/backend/`.
- Keep OSS references under `research/oss-reference/`.
- Keep AGPL references isolated under `research/oss-reference/agpl/`.
- Use cloned OSS repos only for research, reference, selective reuse, or isolated fork.
