# SRS 2.0 Update — Repository Clone Plan, Modular Product Boundaries, and Developer Execution Guide

**Project:** Job Copilot Backend Platform  
**Document type:** SRS 2.0 Addendum / Patch Document  
**Date:** 2026-05-21  
**Status:** To be attached to the existing SRS as an update  
**Purpose:** This document corrects and extends the original SRS by clearly defining which repositories should be cloned, where they should be cloned, which parts should be used as dependencies, which parts should only be studied, and how all modules should remain separable products under the main Core Orchestration Kernel.

---

## 1. Why this SRS 2.0 addendum is required

The first SRS defined the modular architecture, product modules, workflow orchestration, events, database ownership, and human approval model. However, it did **not clearly tell the developer exactly which open-source repositories should be cloned, where they should be cloned, and how they should be used**.

This SRS 2.0 update fixes that gap.

The developer must now follow this rule:

> **Do not clone one external repository and build the product inside it. Create our own main product repository first, then clone selected open-source repositories into `/research/oss-reference/` for study, reference, selective reuse, or isolated fork. The production backend must remain our own modular codebase.**

---

## 2. Updated architecture decision

### 2.1 Main architecture

The system must be built as a **modular monolith first**, not as many deployed microservices.

The platform should have:

```text
One backend application
One primary database initially
Multiple internal product modules
Strict module boundaries
Shared event contracts
Human approval gates
Optional modules kept separate
```

Later, individual modules may become separate services or standalone products.

---

## 3. Product 0 and attachable product modules

The system must follow the “oil pump” model:

```text
Core Kernel = oil pump
Product modules = machines connected to the pump
Events = pipes
Database = storage tanks
Workflow engine = pump controller
Approval queue = safety valve
Audit logs = pressure gauge
```

The Core Kernel moves work from one product module to another. No module should randomly call another module’s internal implementation.

---

## 4. Product/module map

| Product number | Product/module name | Purpose | Can become separate product later? |
|---:|---|---|---|
| P0 | Core Orchestration Kernel | User, campaigns, events, workflow, approval, audit | No, this is base platform |
| P1 | Career Vault | Resume, skills, story, approved claims | Yes |
| P2 | Campaign Planner | Natural language to structured job campaign | Yes |
| P3 | Job Discovery | ATS/job API/company career page ingestion | Yes |
| P4 | Fit Scoring | Resume-to-job matching and decisioning | Yes |
| P5 | Document Generator | Tailored resume, cover letter, change log | Yes |
| P6 | People Finder | Hiring manager/recruiter/referrer discovery | Yes |
| P7 | Outreach Generator | Recruiter email, hiring manager email, referral note, call script | Yes |
| P8 | Review Queue | Human approval before sending/submitting | Yes |
| P9 | Tracker / Job CRM | Application status, follow-ups, events | Yes |
| P10 | Email Discovery Optional | Email candidate generation + verification API | Yes, separate optional module |
| P11 | Autonomous Browsing Optional | Controlled browser automation sandbox | Yes, separate optional module |

---

## 5. Main repository setup

The developer must create **our own repository first**.

### 5.1 Command

```bash
mkdir job-copilot-platform
cd job-copilot-platform
git init
```

### 5.2 Required top-level folder structure

```text
job-copilot-platform/
│
├── apps/
│   └── backend/
│       ├── app/
│       │   ├── main.py
│       │   ├── core_kernel/
│       │   ├── modules/
│       │   │   ├── career_vault/
│       │   │   ├── campaign_planner/
│       │   │   ├── job_discovery/
│       │   │   ├── fit_scoring/
│       │   │   ├── document_generator/
│       │   │   ├── people_finder/
│       │   │   ├── outreach_generator/
│       │   │   ├── review_queue/
│       │   │   ├── tracker/
│       │   │   └── optional/
│       │   │       ├── email_discovery/
│       │   │       └── autonomous_browsing/
│       │   ├── shared/
│       │   │   ├── contracts/
│       │   │   ├── events/
│       │   │   ├── permissions/
│       │   │   ├── observability/
│       │   │   └── utils/
│       │   └── tests/
│       │
│       ├── migrations/
│       ├── docker-compose.yml
│       └── pyproject.toml
│
├── packages/
│   ├── shared-contracts/
│   ├── shared-prompts/
│   └── shared-evals/
│
├── docs/
│   ├── srs/
│   ├── architecture/
│   ├── api-contracts/
│   ├── module-specs/
│   └── decision-records/
│
├── research/
│   └── oss-reference/
│       ├── job-ingestion/
│       ├── resume-document/
│       ├── resume-builders/
│       ├── browser-crawling/
│       ├── ai-workflow/
│       ├── observability/
│       └── agpl/
│
└── README.md
```

---

## 6. Important repository usage rule

All external repositories must be cloned only under:

```text
research/oss-reference/
```

They must **not** be placed under:

```text
apps/backend/app/
```

They must **not** become the main product repo.

They must be treated as:

1. reference material,
2. possible fork source,
3. selective implementation inspiration,
4. isolated optional module,
5. or dependency study.

---

# 7. Repositories to clone

## 7.1 Job ingestion / ATS connector repositories

### 7.1.1 jobber — must clone

**Repository:** `https://github.com/plibither8/jobber.git`  
**Folder:** `research/oss-reference/job-ingestion/jobber/`  
**Use type:** Study, reference, selective reuse, possible fork  
**Reason:** It provides simple API logic to fetch job listings from popular ATS/job boards including Ashby, Greenhouse, Lever, BambooHR, and Workable.

Clone command:

```bash
mkdir -p research/oss-reference/job-ingestion
cd research/oss-reference/job-ingestion
git clone --depth 1 https://github.com/plibither8/jobber.git
```

Use for:

```text
Greenhouse connector
Lever connector
Ashby connector
Workable connector reference
BambooHR connector reference
Job source abstraction ideas
```

Do not allow this repo to own our production schema.

Our production job schema remains inside:

```text
apps/backend/app/modules/job_discovery/
```

---

### 7.1.2 Ever Jobs — clone for architecture reference only

**Repository:** `https://github.com/ever-jobs/ever-jobs.git`  
**Folder:** `research/oss-reference/job-ingestion/ever-jobs/`  
**Use type:** Architecture reference only  
**Reason:** It shows a broader job aggregation architecture and lists many ATS integrations such as Ashby, Greenhouse, Lever, Workable, SmartRecruiters, Workday, Recruitee, Teamtailor, iCIMS, Taleo, SuccessFactors, Jobvite, and others.

Clone command:

```bash
cd research/oss-reference/job-ingestion
git clone --depth 1 https://github.com/ever-jobs/ever-jobs.git
```

Use for:

```text
ATS source list
Connector architecture
Job aggregation architecture
Concurrent source execution ideas
```

Do not copy risky scraping flows. Do not use any LinkedIn scraper or prohibited platform automation.

---

## 7.2 Resume/document parsing repositories

### 7.2.1 Docling — must clone/study and also use as dependency

**Repository:** `https://github.com/docling-project/docling.git`  
**Folder:** `research/oss-reference/resume-document/docling/`  
**Use type:** Dependency + reference  
**Reason:** It is strong for PDF/DOCX/document conversion, resume parsing, JD parsing, and structured document extraction.

Clone command:

```bash
mkdir -p research/oss-reference/resume-document
cd research/oss-reference/resume-document
git clone --depth 1 https://github.com/docling-project/docling.git
```

Production use:

```bash
pip install docling
```

Use for:

```text
Resume parsing
PDF extraction
DOCX extraction
Job description parsing
Document-to-structured-text conversion
Screenshot/document intake where applicable
```

Docling should power the first version of:

```text
P1 Career Vault
P3 Job Discovery JD parser helper
P5 Document Generator input extraction
```

---

### 7.2.2 CV-Matcher — clone for matching reference only

**Repository:** `https://github.com/eristavi/CV-Matcher.git`  
**Folder:** `research/oss-reference/resume-document/CV-Matcher/`  
**Use type:** Reference only  
**Reason:** Useful for ATS-style resume-vs-JD comparison, keyword extraction, and missing keyword logic.

Clone command:

```bash
cd research/oss-reference/resume-document
git clone --depth 1 https://github.com/eristavi/CV-Matcher.git
```

Use for:

```text
Keyword matching ideas
ATS-style scoring ideas
Missing skill detection patterns
Resume/JD comparison workflow
```

Do not use as the final scoring engine.

The final scoring engine must be custom and located at:

```text
apps/backend/app/modules/fit_scoring/
```

---

## 7.3 Resume builder/template repositories

### 7.3.1 Reactive Resume — clone for resume template and future UI reference

**Repository:** `https://github.com/AmruthPillai/Reactive-Resume.git`  
**Folder:** `research/oss-reference/resume-builders/Reactive-Resume/`  
**Use type:** Reference, future UI reference  
**Reason:** Useful for resume section design, resume templates, resume versioning ideas, and future frontend/editor planning.

Clone command:

```bash
mkdir -p research/oss-reference/resume-builders
cd research/oss-reference/resume-builders
git clone --depth 1 https://github.com/AmruthPillai/Reactive-Resume.git
```

Use for:

```text
Resume template architecture
Resume section organization
Resume versioning ideas
Future resume editor reference
```

Do not build our backend inside Reactive Resume.

---

### 7.3.2 OpenResume — clone only inside AGPL folder

**Repository:** `https://github.com/xitanggg/open-resume.git`  
**Folder:** `research/oss-reference/agpl/open-resume/`  
**Use type:** AGPL reference only until license is cleared  
**Reason:** It has resume builder and parser logic, but AGPL code should stay isolated until legal/licensing decision is made.

Clone command:

```bash
mkdir -p research/oss-reference/agpl
cd research/oss-reference/agpl
git clone --depth 1 https://github.com/xitanggg/open-resume.git
```

Use for:

```text
ATS readability ideas
Resume builder UX ideas
Resume parser reference
```

Rule:

```text
Do not copy AGPL code into production until license decision is approved.
```

---

## 7.4 Browser automation and crawling repositories

### 7.4.1 browser-use — clone for autonomous browsing sandbox only

**Repository:** `https://github.com/browser-use/browser-use.git`  
**Folder:** `research/oss-reference/browser-crawling/browser-use/`  
**Use type:** Sandbox only  
**Reason:** Useful for controlled AI browser experiments and form-assist research. It must not be used for LinkedIn scraping, auto-connect, auto-message, or random auto-apply.

Clone command:

```bash
mkdir -p research/oss-reference/browser-crawling
cd research/oss-reference/browser-crawling
git clone --depth 1 https://github.com/browser-use/browser-use.git
```

Allowed use:

```text
Company career page navigation
ATS form-assist experiments
Screenshot-to-browser workflow
Research-only autonomous browsing
```

Disallowed use:

```text
LinkedIn scraping
LinkedIn auto-connect
LinkedIn auto-message
Random auto-apply
Unapproved form submission
```

Production module location:

```text
apps/backend/app/modules/optional/autonomous_browsing/
```

---

### 7.4.2 Crawlee Python — clone for crawler patterns

**Repository:** `https://github.com/apify/crawlee-python.git`  
**Folder:** `research/oss-reference/browser-crawling/crawlee-python/`  
**Use type:** Dependency + reference  
**Reason:** Useful for crawling allowed company career pages and structured site crawling.

Clone command:

```bash
cd research/oss-reference/browser-crawling
git clone --depth 1 https://github.com/apify/crawlee-python.git
```

Production use:

```bash
pip install crawlee
```

Use for:

```text
Allowed public company career page crawling
Career URL discovery
HTML parsing
Crawler retry/storage patterns
```

---

## 7.5 AI workflow and structured output repositories

### 7.5.1 LangGraph — clone for workflow examples

**Repository:** `https://github.com/langchain-ai/langgraph.git`  
**Folder:** `research/oss-reference/ai-workflow/langgraph/`  
**Use type:** Dependency + reference  
**Reason:** Useful for long-running campaign orchestration, human-in-the-loop review, durable execution, retries, and stateful workflow.

Clone command:

```bash
mkdir -p research/oss-reference/ai-workflow
cd research/oss-reference/ai-workflow
git clone --depth 1 https://github.com/langchain-ai/langgraph.git
```

Production use:

```bash
pip install langgraph
```

Use for:

```text
Campaign workflow
Human approval interrupt
Graph-based execution
Workflow state
Retry/resume logic
```

Important:

```text
Pin dependency versions.
Do not allow unsafe arbitrary tool execution.
Add audit logs for every tool/action node.
```

---

### 7.5.2 PydanticAI — clone for structured output examples

**Repository:** `https://github.com/pydantic/pydantic-ai.git`  
**Folder:** `research/oss-reference/ai-workflow/pydantic-ai/`  
**Use type:** Dependency + reference  
**Reason:** Useful for validated JSON output from LLMs.

Clone command:

```bash
cd research/oss-reference/ai-workflow
git clone --depth 1 https://github.com/pydantic/pydantic-ai.git
```

Production use:

```bash
pip install pydantic-ai
```

Use for:

```text
Natural language campaign parsing
Job score JSON
Resume change log JSON
People ranking JSON
Outreach draft JSON
Error-safe structured outputs
```

---

## 7.6 Observability repository

### 7.6.1 Langfuse — clone only if self-hosting/customizing

**Repository:** `https://github.com/langfuse/langfuse.git`  
**Folder:** `research/oss-reference/observability/langfuse/`  
**Use type:** Optional self-hosting/customization reference  
**Reason:** Useful for tracing, prompt versioning, LLM evaluation, cost tracking, and debugging.

Clone command:

```bash
mkdir -p research/oss-reference/observability
cd research/oss-reference/observability
git clone --depth 1 https://github.com/langfuse/langfuse.git
```

If using hosted Langfuse, cloning is optional.

Use for:

```text
Prompt tracing
Job scoring debug
Resume generation debug
People finder debug
LLM cost tracking
Evaluation datasets
```

---

# 8. Tools to install, not clone

The following should normally be installed as dependencies, not cloned as source repositories.

| Tool | Action | Reason |
|---|---|---|
| FastAPI | Install | Core backend API framework |
| Qdrant client | Install | Vector database client |
| Qdrant server | Docker / managed service | Vector search server |
| Prefect | Install | Scheduling/retries |
| Playwright Python | Install | Browser automation library |
| Google API Python Client | Install | Gmail draft creation |
| python-docx | Install | DOCX generation |
| Alembic | Install | Database migrations |
| SQLAlchemy | Install | ORM/data layer |
| PyMuPDF / pypdf if needed | Install | PDF fallback parsing |

Initial install command:

```bash
pip install fastapi uvicorn sqlalchemy alembic pydantic pydantic-ai docling qdrant-client langfuse prefect playwright google-api-python-client python-docx crawlee
playwright install
```

---

# 9. Repositories/tools explicitly not allowed

The developer must not use these:

```text
LinkedIn scrapers
LinkedIn auto-connect tools
LinkedIn auto-message tools
Random auto-apply bots
Old regional resume parsers
Unmaintained resume parsers
Unverified email scraping scripts in core product
Browser agents without allowlist
Any repository with unclear license
Any repository with no working install path
Any repository with no recent maintenance unless used only as reference
```

---

# 10. Email discovery module update

Email discovery must remain separate from the core engine.

Folder:

```text
apps/backend/app/modules/optional/email_discovery/
```

Required submodules:

```text
domain_pattern_finder.py
public_profile_extractor.py
company_contact_page_parser.py
email_candidate_generator.py
email_verification_adapter.py
do_not_contact_guard.py
source_logger.py
```

Required rule:

```text
No verified email → no outbound email draft.
```

The user already has an email verification API. Therefore, this module should only generate email candidates and pass them to the verification API.

The system must store:

```text
email_candidate
source_url
verification_status
verification_provider
verified_at
confidence_score
do_not_contact_status
```

---

# 11. Autonomous browsing module update

Autonomous browsing must remain separate from the core engine.

Folder:

```text
apps/backend/app/modules/optional/autonomous_browsing/
```

Required submodules:

```text
allowed_domains.yaml
browser_session.py
screenshot_extractor.py
page_reader.py
form_prefill_assistant.py
action_logger.py
human_approval_gate.py
robots_policy_checker.py
terms_policy_notes.md
```

Allowed domains:

```text
Company career pages
ATS job forms where automation is allowed
User-owned/internal pages
Public company pages
```

Blocked domains/actions:

```text
LinkedIn scraping
LinkedIn auto-connect
LinkedIn auto-message
Random job auto-apply
Auto-submit without approval
Personal phone scraping
```

---

# 12. Product module ownership update

Each product module must own its own tables. Other modules can read through contracts/APIs/events, not by editing internal tables directly.

| Module | Owns |
|---|---|
| P0 Core Kernel | users, campaigns, workflow_runs, events, audit_logs |
| P1 Career Vault | candidate_profiles, skills, achievements, approved_claims |
| P2 Campaign Planner | campaign_intents, campaign_filters |
| P3 Job Discovery | companies, jobs, job_sources, job_deduplication |
| P4 Fit Scoring | job_scores, score_factors, risk_flags |
| P5 Document Generator | resume_versions, cover_letters, application_packages |
| P6 People Finder | people, contact_candidates, person_sources |
| P7 Outreach Generator | outreach_drafts, message_templates |
| P8 Review Queue | approval_items, approval_history |
| P9 Tracker | application_events, followups, statuses |
| P10 Email Discovery | email_candidates, email_verifications, do_not_contact |
| P11 Autonomous Browsing | browser_sessions, browser_actions, browser_artifacts |

---

# 13. Events that must be added to the SRS

The original SRS must include the following events:

```text
OSSReferencesCloned
OSSReferenceAudited
CampaignCreated
CampaignParsed
CareerVaultCreated
CareerVaultUpdated
JobsDiscovered
JobNormalized
JobDeduplicated
JobScored
JobRejected
ApplicationRecommended
ApplicationPackageCreated
PeopleDiscoveryStarted
PeopleFound
EmailCandidatesGenerated
EmailVerified
OutreachDraftCreated
ReviewRequested
UserApproved
UserRejected
GmailDraftCreated
ApplicationSubmitted
FollowupScheduled
DoNotContactAdded
BrowserSessionStarted
BrowserActionRequested
BrowserActionApproved
BrowserActionRejected
BrowserSessionEnded
```

---

# 14. Developer execution order

The developer must follow this exact order.

## Step 1 — Create our main repo

```bash
mkdir job-copilot-platform
cd job-copilot-platform
git init
```

## Step 2 — Create folder structure

```bash
mkdir -p apps/backend/app/modules
mkdir -p apps/backend/app/core_kernel
mkdir -p apps/backend/app/shared/contracts
mkdir -p apps/backend/app/shared/events
mkdir -p docs/srs docs/architecture docs/api-contracts docs/module-specs docs/decision-records
mkdir -p research/oss-reference
mkdir -p packages/shared-contracts packages/shared-prompts packages/shared-evals
```

## Step 3 — Save this file

Save this document as:

```text
docs/srs/SRS-2.0-Repo-Clone-and-Modular-Build-Update.md
```

## Step 4 — Clone OSS references

Run the clone commands in Section 15.

## Step 5 — Create OSS audit table

Create:

```text
docs/decision-records/ADR-001-OSS-Reference-Audit.md
```

This file must track:

```text
Repo name
Repo URL
Clone date
License
Last commit/release checked
Use type
Allowed production use?
Risk notes
Decision
```

## Step 6 — Build production code separately

Production code must start only in:

```text
apps/backend/app/
```

Do not edit inside `research/oss-reference/` unless intentionally making notes or experiments.

---

# 15. Complete clone command list

```bash
mkdir -p job-copilot-platform/research/oss-reference
cd job-copilot-platform/research/oss-reference

# Job ingestion / ATS
mkdir -p job-ingestion
cd job-ingestion
git clone --depth 1 https://github.com/plibither8/jobber.git
git clone --depth 1 https://github.com/ever-jobs/ever-jobs.git
cd ..

# Resume/document parsing and matching
mkdir -p resume-document
cd resume-document
git clone --depth 1 https://github.com/docling-project/docling.git
git clone --depth 1 https://github.com/eristavi/CV-Matcher.git
cd ..

# Resume builders/templates
mkdir -p resume-builders
cd resume-builders
git clone --depth 1 https://github.com/AmruthPillai/Reactive-Resume.git
cd ..

# AGPL references
mkdir -p agpl
cd agpl
git clone --depth 1 https://github.com/xitanggg/open-resume.git
cd ..

# Browser/crawling sandbox
mkdir -p browser-crawling
cd browser-crawling
git clone --depth 1 https://github.com/browser-use/browser-use.git
git clone --depth 1 https://github.com/apify/crawlee-python.git
cd ..

# Workflow / AI orchestration
mkdir -p ai-workflow
cd ai-workflow
git clone --depth 1 https://github.com/langchain-ai/langgraph.git
git clone --depth 1 https://github.com/pydantic/pydantic-ai.git
cd ..

# Observability, only if self-hosting/customizing
mkdir -p observability
cd observability
git clone --depth 1 https://github.com/langfuse/langfuse.git
cd ..
```

---

# 16. Patch to add to original SRS

Add this section near the beginning of the original SRS.

## SRS 2.0 Repository Strategy

The system must not be built inside any third-party open-source repository. The product must have its own repository named `job-copilot-platform`.

All external repositories must be cloned under:

```text
research/oss-reference/
```

They must be used only for research, selective reuse, implementation reference, or isolated fork. The production backend must remain under:

```text
apps/backend/
```

The developer must clone and audit the following repositories before coding job ingestion, document parsing, browser automation, AI orchestration, or resume generation:

```text
jobber
ever-jobs
docling
CV-Matcher
Reactive Resume
OpenResume
browser-use
crawlee-python
LangGraph
PydanticAI
Langfuse
```

No LinkedIn scraper, random auto-apply bot, old regional parser, or unmaintained script may be used as a core dependency.

---

# 17. Acceptance criteria for SRS 2.0

The SRS 2.0 update is accepted only if:

```text
[ ] Main repo is created separately.
[ ] All external repos are cloned only under research/oss-reference.
[ ] No production code exists inside cloned OSS repos.
[ ] OSS audit file is created.
[ ] Each repo has a use decision: dependency, reference, fork, sandbox, reject.
[ ] AGPL code is isolated.
[ ] LinkedIn scraping is explicitly blocked.
[ ] Email discovery is a separate optional module.
[ ] Autonomous browsing is a separate optional module.
[ ] Core production modules remain under apps/backend/app/modules.
[ ] Each module has input/output contracts.
[ ] Each module emits events instead of directly modifying other modules.
[ ] Review queue blocks sending/submitting until approval.
```

---

# 18. What the developer should do immediately

The developer should perform the following:

```text
1. Create the main repo.
2. Create folder structure.
3. Add original SRS to docs/srs.
4. Add this SRS 2.0 file to docs/srs.
5. Clone OSS references into research/oss-reference.
6. Create ADR-001-OSS-Reference-Audit.md.
7. Audit each cloned repo for license, freshness, installability, and relevance.
8. Start coding only the production modular backend skeleton under apps/backend/app.
```

---

# 19. Final instruction to developer

> Build our own backend. Use open-source repositories only as references, dependencies, or isolated modules. Do not build inside any external repo. Do not use LinkedIn scrapers, random auto-apply bots, or old regional parsers. Keep email discovery and autonomous browsing separate. Keep all modules contract-first so any product module can later be separated from the main platform.

---

# 20. Source reference URLs

These URLs are included so the developer can verify repositories manually before using them.

```text
jobber:
https://github.com/plibither8/jobber

Ever Jobs:
https://github.com/ever-jobs/ever-jobs

Docling:
https://github.com/docling-project/docling

Docling releases:
https://github.com/docling-project/docling/releases

CV-Matcher:
https://github.com/eristavi/CV-Matcher

Reactive Resume:
https://github.com/AmruthPillai/Reactive-Resume

OpenResume:
https://github.com/xitanggg/open-resume

browser-use:
https://github.com/browser-use/browser-use

browser-use releases:
https://github.com/browser-use/browser-use/releases

Crawlee Python:
https://github.com/apify/crawlee-python

LangGraph:
https://github.com/langchain-ai/langgraph

PydanticAI:
https://github.com/pydantic/pydantic-ai

Langfuse:
https://github.com/langfuse/langfuse
```

