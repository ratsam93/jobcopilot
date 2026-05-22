# Job Copilot Backend Tasks

## Setup

- [X] S1 Create the backend repository structure and ignore files.
- [X] S2 Add the base FastAPI application skeleton and config entrypoints.
- [X] S3 Add local development and container orchestration files.
- [X] S4 Add a migration and database bootstrap path.
- [X] S5 Document the SRS 2.0 repository strategy and OSS audit layout.

## Core Foundation

- [X] C1 Implement core kernel module registry and workflow state model.
- [X] C2 Implement audit logging and trace-id propagation.
- [X] C3 Implement permissions and approval gate primitives.
- [X] C4 Add shared event and schema contracts.

## Career Vault

- [X] V1 Implement resume upload endpoint and file handling.
- [X] V2 Implement resume parsing and profile creation.
- [X] V3 Store skills, claims, and do-not-claim data.

## Campaign Planning

- [X] P1 Implement natural-language campaign creation.
- [X] P2 Validate structured campaign output with Pydantic.
- [X] P3 Expose campaign status and job list endpoints.

## Job Discovery and Scoring

- [X] J1 Implement job source adapters and normalization.
- [X] J2 Implement deduplication and persistence.
- [X] J3 Implement fit scoring rules and explanations.

## Application Package Generation

- [X] A1 Implement tailored resume generation.
- [X] A2 Implement cover letter generation and unsupported-claim detection.
- [X] A3 Persist package artifacts and change logs.

## People and Outreach

- [X] O1 Implement people discovery and ranking.
- [X] O2 Implement email candidate generation and verification adapter.
- [X] O3 Implement outreach draft generation.

## Review, Gmail, and Tracking

- [X] R1 Implement review queue workflows and approval endpoints.
- [X] R2 Implement Gmail draft creation after approval.
- [X] R3 Implement application tracker and follow-up scheduling.

## Validation

- [X] T1 Add integration tests for resume to campaign flow.
- [X] T2 Add integration tests for campaign to discovery and scoring.
- [X] T3 Add integration tests for package, review, Gmail draft, and tracker.
- [X] T4 Add safety tests for LinkedIn blocking, approval gating, and claim validation.
