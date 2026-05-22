# ADR-001 OSS Reference Audit

## Decision

Use selected open-source repositories only as research/reference material under `research/oss-reference/`. Keep production code in `apps/backend/`.

## Audit Fields

| Repo name | Repo URL | Clone date | License | Last commit/release checked | Use type | Allowed production use? | Risk notes | Decision |
|---|---|---|---|---|---|---|---|---|
| jobber | https://github.com/plibither8/jobber | 2026-05-21 | TBD | TBD | Study/reference/selective reuse | No direct dependency | Connector ideas only | Keep as reference |
| ever-jobs | https://github.com/ever-jobs/ever-jobs | 2026-05-21 | TBD | TBD | Architecture reference | No | Avoid risky scraping logic | Keep as reference |
| docling | https://github.com/docling-project/docling | 2026-05-21 | TBD | TBD | Dependency + reference | Yes, as dependency | Verify install/version pinning | Keep as dependency/reference |
| CV-Matcher | https://github.com/eristavi/CV-Matcher | 2026-05-21 | TBD | TBD | Reference only | No | Scoring ideas only | Keep as reference |
| Reactive-Resume | https://github.com/AmruthPillai/Reactive-Resume | 2026-05-21 | TBD | TBD | Reference | No | Template/reference only | Keep as reference |
| open-resume | https://github.com/xitanggg/open-resume | 2026-05-21 | AGPL-3.0 | TBD | AGPL reference | No until reviewed | License isolation required | Keep isolated |
| browser-use | https://github.com/browser-use/browser-use | 2026-05-21 | TBD | TBD | Sandbox reference | No direct production dependency | Must remain allowlisted | Keep as sandbox reference |
| crawlee-python | https://github.com/apify/crawlee-python | 2026-05-21 | TBD | TBD | Dependency + reference | Yes, as dependency | Verify crawl scope | Keep as dependency/reference |
| langgraph | https://github.com/langchain-ai/langgraph | 2026-05-21 | TBD | TBD | Dependency + reference | Yes, as dependency | Pin versions, review tool execution | Keep as dependency/reference |
| pydantic-ai | https://github.com/pydantic/pydantic-ai | 2026-05-21 | TBD | TBD | Dependency + reference | Yes, as dependency | Validate structured outputs | Keep as dependency/reference |
| langfuse | https://github.com/langfuse/langfuse | 2026-05-21 | TBD | TBD | Optional self-host/customize | No by default | Only clone if self-hosting | Keep optional |

