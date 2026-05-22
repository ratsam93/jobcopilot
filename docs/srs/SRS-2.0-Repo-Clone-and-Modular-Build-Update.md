# SRS 2.0 Update - Repository Clone Plan, Modular Product Boundaries, and Developer Execution Guide

This file mirrors the SRS 2.0 addendum in the repository root and is the version that should be treated as the formal attached update under `docs/srs/`.

## Repository Strategy

- Create the main repo first: `job-copilot-platform`
- Keep production code in `apps/backend/`
- Clone external repos only under `research/oss-reference/`
- Keep AGPL references isolated under `research/oss-reference/agpl/`

## Clone Areas

- `research/oss-reference/job-ingestion/`
- `research/oss-reference/resume-document/`
- `research/oss-reference/resume-builders/`
- `research/oss-reference/browser-crawling/`
- `research/oss-reference/ai-workflow/`
- `research/oss-reference/observability/`

## Production Rule

Do not build the product inside any cloned OSS repository. Use those repositories for study, reference, selective reuse, or isolated fork only.

