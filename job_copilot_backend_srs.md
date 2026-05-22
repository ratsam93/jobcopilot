# Software Requirements Specification (SRS)

# Modular AI Job Search, Application, Internal Outreach & Career Campaign Backend

**Document Type:** Software Requirements Specification  
**Version:** 1.0  
**Date:** 2026-05-21  
**Prepared For:** Product owner and backend developer team  
**Primary Build Strategy:** Backend-first modular monolith with contract-first product modules  
**Frontend Status:** Not in scope for MVP; backend must be usable through API, Postman, CLI, and scheduled workers first  

---

## 0. Executive Summary

This document specifies an AI-powered backend system that helps a candidate discover relevant jobs, score them against their resume and career story, generate tailored application assets, identify internal company contacts such as recruiters and hiring managers, prepare outreach drafts, and track the entire job-search process.

The system must **not** be built as one large unstructured bot. It must be built as a **modular product-orchestration platform** where each major capability is treated as a product module that can later be separated, reused, or sold independently.

The recommended architecture is:

```text
Product 0: Core Orchestration Kernel
Products 1-11: Independent attachable product modules
```

The Core Orchestration Kernel acts as the “oil pump.” It moves data between product modules, controls workflow state, blocks unsafe actions until approval, logs what happened, and allows any module to be replaced without breaking the full system.

The first release must focus on the backend engine only. The backend must support natural language job campaigns such as:

```text
Apply to top technology companies across the USA where I am fit.
```

The backend must convert such a request into a structured campaign, discover jobs, score jobs, create tailored resumes/letters, find internal people, draft outreach, and wait for human approval before any sending/submission.

---

## 1. Product Vision

### 1.1 Product Vision Statement

Build a backend platform that turns job search into a structured, intelligent, reviewable career sales pipeline.

The system should allow a user to say, in natural language:

```text
Find me the best remote AI/product/consulting jobs at top US tech companies where I fit, prepare my resume, create cover letters, find the right internal people, and prepare outreach.
```

The system should then perform the backend work required to:

1. Understand the user’s intent.
2. Use the user’s resume and career vault as the source of truth.
3. Discover relevant jobs through public/allowed sources.
4. Normalize and deduplicate jobs.
5. Score each job against the candidate’s profile.
6. Generate job-specific application packages.
7. Find recruiters, hiring managers, and possible internal referrers.
8. Generate outreach drafts and call scripts.
9. Hold all final actions in an approval queue.
10. Track applications, follow-ups, and outcomes.

### 1.2 Product Philosophy

The product must operate as an **application copilot**, not a blind auto-apply spam tool.

The system must prioritize:

- Quality over volume.
- Fit over random application count.
- Verified sources over scraped data.
- Human approval over unsafe automation.
- Modular architecture over one-off scripts.
- Reusable product modules over hardcoded workflows.
- Auditability and compliance over speed.

### 1.3 Core Differentiator

Most job automation systems only do:

```text
Find job -> Apply
```

This product must do:

```text
Understand career profile
-> Discover jobs
-> Score fit
-> Create tailored application package
-> Find internal people
-> Prepare personalized outreach
-> Require human approval
-> Track follow-ups and outcomes
```

---

## 2. Scope

### 2.1 In Scope for Backend MVP

The MVP backend must include:

1. User and candidate profile management.
2. Resume upload and parsing.
3. Career Vault creation.
4. Natural language campaign parsing.
5. Job discovery through APIs and ATS connectors.
6. Job normalization and deduplication.
7. Job fit scoring.
8. Application package generation.
9. Hiring manager/recruiter/referrer discovery.
10. Email candidate generation and verification through the user’s email verification API.
11. Outreach draft generation.
12. Gmail draft creation only, not automatic sending.
13. Review and approval queue.
14. Application tracker.
15. Audit logging.
16. Observability and LLM trace logging.
17. Optional controlled autonomous browsing sandbox.

### 2.2 Out of Scope for Backend MVP

The following are explicitly out of scope for the MVP:

1. Full frontend UI.
2. Blind auto-apply to all jobs.
3. LinkedIn scraping.
4. LinkedIn auto-connect.
5. LinkedIn auto-message.
6. Random job form submission without review.
7. Personal phone scraping.
8. Use of unverified personal email addresses for outreach.
9. Use of old/unmaintained resume parsers as core dependency.
10. Mass email sending.
11. Resume claims not grounded in the Career Vault.
12. Complex analytics dashboard.
13. Mobile app.
14. Paid marketplace.
15. Multi-user enterprise controls beyond basic user isolation.

### 2.3 Future Scope

Future versions may include:

1. Frontend dashboard.
2. Browser-based form prefill assistant.
3. Calendar follow-up reminders.
4. Interview preparation engine.
5. Voice/calling assistant.
6. Career coaching module.
7. Standalone resume scoring API.
8. Standalone job discovery API.
9. Standalone hiring manager finder.
10. Multi-user recruitment/career-coaching SaaS.

---

## 3. Architecture Decision

### 3.1 Recommended Architecture

The system must begin as a **modular monolith**, not as many separate microservices.

Reason:

- The product boundaries are known conceptually but will evolve during development.
- A modular monolith is faster to build and debug.
- Module boundaries can be enforced through internal APIs, contracts, and database ownership.
- Later, any mature module can be extracted into a separate service.

### 3.2 Modular Monolith Rules

The backend will be one deployable application, but internally divided into strict modules:

```text
core_kernel/
modules/
  career_vault/
  campaign_planner/
  job_discovery/
  fit_scoring/
  document_generator/
  people_finder/
  outreach_generator/
  review_queue/
  tracker/
  optional/email_discovery/
  optional/autonomous_browsing/
```

Each module must have:

1. Its own service layer.
2. Its own schemas.
3. Its own database tables or table namespace.
4. Its own test suite.
5. Its own public contract.
6. Its own events consumed/emitted.
7. Its own error types.
8. Its own acceptance criteria.
9. No direct access to another module’s private implementation.

### 3.3 Why Not Microservices First

Do not create many deployed services initially because:

- Developer effort will increase too much.
- Debugging workflows will become harder.
- Database boundaries may not yet be stable.
- The frontend does not exist yet.
- The main risk is product logic, not scaling.

### 3.4 Future Extraction Strategy

Any module can become a separate product if it has:

1. Stable input/output contracts.
2. Independent demand.
3. Clear database ownership.
4. Clear API boundary.
5. No direct internal imports from other modules.
6. Enough usage to justify extraction.

Possible future standalone products:

| Module | Standalone Product Possibility |
|---|---|
| Career Vault | AI Career Profile Manager |
| Campaign Planner | Natural Language Career Campaign Planner |
| Job Discovery | Job Feed Intelligence API |
| Fit Scoring | Resume-to-Job Fit Scoring API |
| Document Generator | Tailored Resume & Letter Generator |
| People Finder | Hiring Manager Finder |
| Outreach Generator | AI Job Outreach Writer |
| Tracker | Job Search CRM |
| Email Discovery | Professional Email Discovery Tool |
| Autonomous Browsing | Form Prefill / Research Assistant |

---

## 4. Orchestration Model

### 4.1 Core Concept

The system must use a hybrid model:

```text
Central orchestration for main campaign flow
+ Event-driven communication between modules
```

The Core Kernel controls major campaign execution. Modules emit events when they complete work. Other modules may react to events when appropriate.

### 4.2 Oil Pump Analogy

The Core Kernel is the oil pump:

| Analogy | System Component |
|---|---|
| Oil pump | Core Orchestration Kernel |
| Pipes | Event bus and contracts |
| Tanks/machines | Product modules |
| Pressure gauge | Logs, observability, status |
| Safety valve | Review and approval queue |
| Oil flow | Data moving through job campaign |

The pump must:

1. Pull input from one module.
2. Push it to the next module.
3. Check safety status.
4. Pause when approval is required.
5. Resume when approved.
6. Log every transition.
7. Stop if a module fails.
8. Allow the failed module to retry or be replaced.

### 4.3 Main Campaign Flow

```text
Natural language command
-> Campaign Planner
-> Campaign Created
-> Job Discovery
-> Jobs Normalized
-> Fit Scoring
-> A-grade/B-grade/Rejected jobs
-> Application Package Generation
-> People Finder
-> Email Discovery/Verification
-> Outreach Generator
-> Review Queue
-> Gmail Draft Creation
-> Application Tracker
-> Follow-up Scheduler
```

### 4.4 Required Workflow States

A campaign must support these states:

```text
created
parsed
job_discovery_queued
job_discovery_running
jobs_discovered
jobs_normalized
jobs_scored
application_generation_running
application_packages_created
people_discovery_running
people_found
outreach_generation_running
outreach_drafts_created
review_pending
approved_for_execution
partially_approved
rejected
completed
failed
paused
cancelled
```

### 4.5 Required Job States

Each job must support these states:

```text
discovered
normalized
duplicate
scoring_pending
scored
rejected_low_fit
saved_for_later
recommended
package_pending
package_created
people_pending
people_found
outreach_pending
review_pending
approved
applied
outreach_sent
followup_scheduled
interviewing
rejected_by_company
closed
expired
```

---

## 5. Product Numbering and Module Boundaries

### 5.1 Product List

| Product Number | Name | Required for MVP | Can Become Separate Product |
|---:|---|---|---|
| P0 | Core Orchestration Kernel | Yes | Platform base |
| P1 | Career Vault | Yes | Yes |
| P2 | Natural Language Campaign Planner | Yes | Yes |
| P3 | Job Discovery Engine | Yes | Yes |
| P4 | Job Fit Scoring Engine | Yes | Yes |
| P5 | Resume & Letter Generator | Yes | Yes |
| P6 | People Finder / Internal Access Engine | Yes | Yes |
| P7 | Outreach Generator | Yes | Yes |
| P8 | Review & Approval Queue | Yes | Yes |
| P9 | Application Tracker / Job CRM | Yes | Yes |
| P10 | Email Discovery Module | Optional MVP, but planned | Yes |
| P11 | Autonomous Browsing Sandbox | Optional MVP, but planned | Yes |

### 5.2 Module Boundary Rule

A module may only communicate with another module through:

1. Public service contract.
2. API endpoint.
3. Event.
4. Shared read model approved by the Core Kernel.

A module must not directly import another module’s private services.

Bad:

```python
from modules.career_vault.internal.parser import private_parse_resume
```

Good:

```python
career_profile = career_vault_client.get_profile(candidate_profile_id)
```

### 5.3 Database Ownership Rule

Each module owns its tables. Other modules read/write only through public service methods or controlled read models.

| Module | Owns Tables Prefix |
|---|---|
| P0 Core Kernel | core_*, audit_*, events_* |
| P1 Career Vault | career_* |
| P2 Campaign Planner | campaign_* |
| P3 Job Discovery | job_*, company_*, source_* |
| P4 Fit Scoring | score_* |
| P5 Document Generator | doc_*, package_* |
| P6 People Finder | people_*, contact_* |
| P7 Outreach Generator | outreach_* |
| P8 Review Queue | review_* |
| P9 Tracker | tracker_*, application_* |
| P10 Email Discovery | email_* |
| P11 Autonomous Browsing | browser_* |

---

## 6. Technology Stack Requirements

### 6.1 Backend API

Use **FastAPI** for the backend API.

Requirements:

- Python-based backend.
- Auto-generated OpenAPI docs.
- Pydantic schemas.
- Easy Postman testing.
- Async support.
- Works well with AI/document processing workflows.

### 6.2 Database

Use PostgreSQL for primary relational data.

Requirements:

- Store users, campaigns, jobs, people, packages, drafts, approvals, and tracker records.
- Support migrations.
- Support JSONB fields for structured AI outputs.
- Support strict foreign keys for critical relationships.

### 6.3 Vector Database

Use Qdrant for semantic search and matching.

Requirements:

- Store resume chunks.
- Store achievement chunks.
- Store job description embeddings.
- Store company intelligence chunks.
- Support metadata payload filtering by user, campaign, module, source, and object type.

### 6.4 Workflow Orchestration

Use LangGraph-style stateful orchestration for AI workflows.

Requirements:

- Long-running campaign flows.
- Human-in-the-loop pauses.
- Resume/retry from last known state.
- Store workflow checkpoints.
- Allow side effects to be isolated in nodes/tasks.

### 6.5 Background Jobs

Use Prefect, Celery, or equivalent worker system.

MVP acceptable option:

- Use Prefect for scheduled workflows and retries.
- Use Redis for queueing if using Celery/RQ later.

Required background jobs:

1. Campaign execution.
2. Job ingestion.
3. Job scoring.
4. Resume generation.
5. People discovery.
6. Email verification.
7. Draft creation.
8. Follow-up reminders.
9. Stale job refresh.
10. Failed task retry.

### 6.6 Document Parsing

Use Docling as the primary document parser.

Requirements:

- Parse PDF resumes.
- Parse DOCX resumes.
- Parse job descriptions.
- Parse uploaded screenshots/documents if needed.
- Extract text and layout metadata when available.

### 6.7 Structured AI Outputs

Use PydanticAI or equivalent Pydantic-based validation for model outputs.

Requirements:

- Every LLM output that affects workflow must be validated.
- No downstream module should rely on free-form text when JSON is expected.
- Invalid outputs must trigger retry or manual review.

### 6.8 Observability

Use Langfuse or equivalent LLM observability system.

Requirements:

- Track prompt version.
- Track model response.
- Track cost/latency.
- Track evaluation score.
- Track hallucination/unsupported-claim flags.
- Debug why a job was scored high or low.

### 6.9 Browser Automation

Use Playwright for controlled browser operations.

Rules:

- Browser automation must be optional.
- Must be domain allowlisted.
- Must log every action.
- Must never automate LinkedIn actions.
- Must stop before final submission unless explicit user approval exists.

### 6.10 Email Integration

Use Gmail API for draft creation.

Rules:

- MVP creates drafts only.
- Sending requires explicit user approval.
- Store Gmail draft IDs.
- Support updating drafts before send.

### 6.11 Email Verification

The user already has an email verification API. The system must integrate with it.

Rules:

- No outreach draft to an email unless it is verified or manually approved.
- Store verification result.
- Store verification timestamp.
- Store source used to generate the email candidate.
- Never scrape personal emails as primary target.

---

## 7. User Roles and Permissions

### 7.1 Roles

MVP roles:

| Role | Description |
|---|---|
| Owner/User | The candidate using the system for their own job search |
| Admin/Developer | Technical user with access to configuration and logs |
| System Worker | Background process running module tasks |

Future roles:

| Role | Description |
|---|---|
| Career Coach | Can review applications but not send |
| Recruiter User | Uses fit scoring/job discovery as separate product |
| Team Admin | Manages multiple candidate profiles |

### 7.2 Permission Rules

1. Only the user can approve sending an email.
2. Only the user can approve final application submission.
3. Workers can generate drafts but cannot send unless approval exists.
4. Developers can view logs but should not access sensitive resume data in production without permission.
5. Any module touching external communication must check approval status.

---

## 8. Key Definitions

| Term | Meaning |
|---|---|
| Career Vault | Structured source of truth about candidate resume, skills, claims, preferences, and career story |
| Campaign | A natural-language job search mission converted into structured execution plan |
| Job Discovery | Process of finding jobs from APIs, ATS, company pages, and allowed sources |
| Job Normalization | Converting source-specific job fields into the internal job schema |
| Fit Score | Numeric score showing candidate-job alignment |
| A-grade Job | High-fit job that should receive application package and outreach |
| Application Package | Tailored resume, cover letter, fit summary, and outreach material for one job |
| People Finder | Module that discovers recruiter/hiring manager/referrer candidates |
| Outreach Draft | Email/message/call script generated but not sent |
| Review Queue | Human approval layer before sending/submitting |
| Execution Mode | Controls whether system only drafts or can act after approval |
| Do-Not-Contact | Person/email/company that must not receive further outreach |

---

## 9. High-Level Data Flow

```text
1. User uploads resume
2. Career Vault parses and structures profile
3. User creates campaign in natural language
4. Campaign Planner creates structured campaign plan
5. Job Discovery fetches jobs from allowed sources
6. Job Normalizer standardizes and deduplicates jobs
7. Fit Scoring scores jobs against Career Vault
8. Application Generator creates packages for selected jobs
9. People Finder discovers internal contacts
10. Email Discovery generates and verifies professional emails where applicable
11. Outreach Generator writes emails/messages/call scripts
12. Review Queue waits for approval
13. Gmail Draft Engine creates draft emails after approval or before approval depending on configuration
14. Tracker records all activity and follow-ups
```

---

## 10. Functional Requirements by Product Module

# P0. Core Orchestration Kernel

## P0.1 Purpose

The Core Orchestration Kernel is the central platform layer. It coordinates modules, maintains workflow state, handles events, controls approvals, logs actions, and enforces safety/compliance rules.

## P0.2 Responsibilities

The Core Kernel must:

1. Register modules.
2. Maintain user identity.
3. Maintain campaign state.
4. Start and stop workflows.
5. Route events.
6. Enforce approval requirements.
7. Store audit logs.
8. Manage file references.
9. Manage configuration.
10. Enforce module boundaries.
11. Track errors and retries.
12. Provide health-check endpoints.

## P0.3 Non-Responsibilities

The Core Kernel must not:

1. Parse resumes.
2. Discover jobs directly.
3. Score jobs directly.
4. Generate resume content directly.
5. Find emails directly.
6. Send emails directly.

It coordinates modules that do those tasks.

## P0.4 Main Entities

### core_users

| Field | Type | Required | Notes |
|---|---|---:|---|
| id | UUID | Yes | Primary key |
| name | String | Yes | User name |
| email | String | Yes | Login/contact email |
| timezone | String | Yes | Default Asia/Kolkata if unknown |
| created_at | Timestamp | Yes |  |
| updated_at | Timestamp | Yes |  |

### core_module_registry

| Field | Type | Required | Notes |
|---|---|---:|---|
| id | UUID | Yes |  |
| module_key | String | Yes | e.g. career_vault |
| module_name | String | Yes |  |
| version | String | Yes | Semantic version |
| enabled | Boolean | Yes |  |
| config_json | JSONB | No | Module settings |
| created_at | Timestamp | Yes |  |

### core_workflow_runs

| Field | Type | Required | Notes |
|---|---|---:|---|
| id | UUID | Yes |  |
| campaign_id | UUID | Yes |  |
| workflow_type | String | Yes | campaign_run, scoring_run, people_run |
| status | String | Yes | running, paused, failed, completed |
| current_node | String | No | Current orchestration node |
| started_at | Timestamp | Yes |  |
| completed_at | Timestamp | No |  |
| error_json | JSONB | No |  |

### audit_logs

| Field | Type | Required | Notes |
|---|---|---:|---|
| id | UUID | Yes |  |
| user_id | UUID | Yes |  |
| entity_type | String | Yes | campaign/job/person/draft/etc. |
| entity_id | UUID | No |  |
| action | String | Yes | created/scored/generated/approved/etc. |
| actor_type | String | Yes | user/system/admin/worker |
| details_json | JSONB | No |  |
| created_at | Timestamp | Yes |  |

## P0.5 Events Owned

The Core Kernel owns the event envelope, not all event types.

### Event Envelope

```json
{
  "event_id": "uuid",
  "event_type": "CampaignCreated",
  "event_version": "1.0",
  "source_module": "campaign_planner",
  "user_id": "uuid",
  "campaign_id": "uuid",
  "entity_type": "campaign",
  "entity_id": "uuid",
  "payload": {},
  "created_at": "2026-05-21T10:00:00Z",
  "correlation_id": "uuid",
  "causation_id": "uuid"
}
```

## P0.6 Required APIs

```http
GET  /health
GET  /modules
POST /modules/{module_key}/enable
POST /modules/{module_key}/disable
GET  /workflows/{workflow_run_id}
POST /workflows/{workflow_run_id}/pause
POST /workflows/{workflow_run_id}/resume
POST /workflows/{workflow_run_id}/cancel
GET  /audit-logs
GET  /events
```

## P0.7 Acceptance Criteria

1. Developer can register a module with a module key and version.
2. Campaign workflow state is visible through API.
3. Every major system action creates an audit log.
4. A failed workflow can be inspected with error details.
5. A paused workflow can resume from the correct node.
6. A disabled module cannot be invoked.

---

# P1. Career Vault

## P1.1 Purpose

The Career Vault stores the candidate’s verified career truth. It is the only source that resume tailoring, fit scoring, and outreach personalization can use for candidate facts.

## P1.2 Responsibilities

Career Vault must:

1. Accept resume uploads.
2. Parse PDF/DOCX resumes.
3. Extract contact info, experience, education, skills, projects, certifications, achievements.
4. Create structured candidate profile.
5. Store approved claims.
6. Store do-not-claim items.
7. Store salary, location, remote, role preferences.
8. Store career story.
9. Store reusable resume bullets.
10. Store career-track mapping.
11. Provide profile data to other modules through API.
12. Track profile versions.

## P1.3 Non-Responsibilities

Career Vault must not:

1. Decide which jobs to apply to.
2. Generate final tailored resume documents.
3. Find jobs.
4. Find people.
5. Send outreach.

## P1.4 Career Vault Objects

### Candidate Profile

```json
{
  "candidate_profile_id": "uuid",
  "user_id": "uuid",
  "full_name": "Sam",
  "primary_email": "user@example.com",
  "phone": null,
  "location": "India",
  "timezone": "Asia/Kolkata",
  "career_story": "...",
  "target_roles": [
    "AI Consultant",
    "Solutions Consultant",
    "GTM Manager",
    "Learning Technology Consultant"
  ],
  "target_geographies": ["USA", "Remote", "Global Remote"],
  "salary_target": {
    "minimum_usd": 30000,
    "ideal_usd": 100000
  },
  "remote_preference": "required_for_lower_compensation",
  "work_authorization_notes": "Must be confirmed per role",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Skill Object

```json
{
  "skill_id": "uuid",
  "candidate_profile_id": "uuid",
  "skill_name": "AI automation",
  "skill_category": "technical/business/domain",
  "evidence": "Used in project X",
  "confidence": 0.9,
  "approved": true,
  "source": "resume/manual/user_confirmed"
}
```

### Approved Claim Object

```json
{
  "claim_id": "uuid",
  "candidate_profile_id": "uuid",
  "claim_text": "Built AI-driven workflow automation for corporate learning use cases.",
  "claim_type": "achievement/project/skill/result",
  "source": "resume/user_confirmed/email/project_note",
  "approved": true,
  "can_use_in_resume": true,
  "can_use_in_email": true
}
```

### Do-Not-Claim Object

```json
{
  "id": "uuid",
  "candidate_profile_id": "uuid",
  "blocked_claim": "Do not claim direct Salesforce implementation experience",
  "reason": "Not verified",
  "created_at": "timestamp"
}
```

## P1.5 Database Tables

### career_profiles

| Field | Type | Required |
|---|---|---:|
| id | UUID | Yes |
| user_id | UUID | Yes |
| full_name | String | Yes |
| primary_email | String | No |
| phone | String | No |
| location | String | No |
| timezone | String | Yes |
| career_story | Text | No |
| target_roles_json | JSONB | No |
| target_geographies_json | JSONB | No |
| salary_json | JSONB | No |
| remote_preference | String | No |
| status | String | Yes |
| created_at | Timestamp | Yes |
| updated_at | Timestamp | Yes |

### career_resume_files

| Field | Type | Required |
|---|---|---:|
| id | UUID | Yes |
| candidate_profile_id | UUID | Yes |
| file_name | String | Yes |
| file_type | String | Yes |
| storage_url | String | Yes |
| parsed_text | Text | No |
| parser_name | String | No |
| parser_version | String | No |
| parse_status | String | Yes |
| created_at | Timestamp | Yes |

### career_skills

Fields: id, candidate_profile_id, skill_name, skill_category, evidence_text, confidence, approved, source, created_at, updated_at.

### career_experiences

Fields: id, candidate_profile_id, company_name, title, start_date, end_date, description, achievements_json, source, approved.

### career_projects

Fields: id, candidate_profile_id, project_name, domain, description, tools_json, outcomes_json, approved.

### career_approved_claims

Fields: id, candidate_profile_id, claim_text, claim_type, source, approved, can_use_in_resume, can_use_in_email, created_at.

### career_do_not_claim

Fields: id, candidate_profile_id, blocked_claim, reason, created_at.

### career_bullet_bank

Fields: id, candidate_profile_id, bullet_text, category, role_track, evidence_source, approved, created_at.

## P1.6 APIs

```http
POST /career-vault/resume/upload
GET  /career-vault/profile/{candidate_profile_id}
POST /career-vault/profile/{candidate_profile_id}/update
GET  /career-vault/profile/{candidate_profile_id}/skills
POST /career-vault/profile/{candidate_profile_id}/skills
POST /career-vault/profile/{candidate_profile_id}/approved-claims
POST /career-vault/profile/{candidate_profile_id}/do-not-claim
GET  /career-vault/profile/{candidate_profile_id}/bullet-bank
POST /career-vault/profile/{candidate_profile_id}/bullet-bank
```

## P1.7 Events Emitted

```text
ResumeUploaded
ResumeParsed
CareerProfileCreated
CareerProfileUpdated
SkillApproved
ClaimApproved
DoNotClaimAdded
```

## P1.8 Events Consumed

```text
UserCreated
ApplicationPackageRejectedForUnsupportedClaim
```

## P1.9 Error States

| Error | Handling |
|---|---|
| Unsupported file type | Reject upload with user-readable message |
| Parser failed | Mark parse_status failed and allow retry/manual paste |
| Empty resume text | Request manual text input |
| Duplicate resume upload | Keep new version, mark old version inactive if user chooses |
| Claim conflict | Put in manual review |

## P1.10 Acceptance Criteria

1. User can upload PDF or DOCX resume.
2. System extracts text and creates structured profile.
3. User can add or edit target roles.
4. User can mark a claim as approved.
5. User can add do-not-claim constraints.
6. Other modules can retrieve only approved claims.
7. Resume tailoring cannot use unapproved claims.

---

# P2. Natural Language Campaign Planner

## P2.1 Purpose

The Campaign Planner converts a vague natural language instruction into a structured campaign plan.

Example:

```text
Apply to top technology companies across the USA where I am fit.
```

Must become:

```json
{
  "campaign_name": "Top US Technology Companies",
  "target_country": "United States",
  "company_types": ["technology", "SaaS", "AI", "cloud", "product"],
  "role_family": "auto_detect_from_career_vault",
  "work_modes": ["remote", "global_remote", "us_remote"],
  "minimum_fit_score": 75,
  "include_resume": true,
  "include_cover_letter": true,
  "include_people_finder": true,
  "include_outreach": true,
  "execution_mode": "draft_only_until_approved"
}
```

## P2.2 Responsibilities

1. Accept natural language campaign prompts.
2. Infer structured search criteria.
3. Ask for clarification only when truly necessary.
4. Use Career Vault to infer role families.
5. Create campaign records.
6. Set execution mode.
7. Set safety constraints.
8. Emit campaign events.

## P2.3 Execution Modes

| Mode | Meaning |
|---|---|
| research_only | Find jobs/people only; generate no application documents |
| draft_only | Generate documents/drafts; do not send/submit |
| approval_required | Generate and create drafts; execution only after approval |
| manual_execution | Prepare everything; user manually sends/applies |

Default mode must be:

```text
approval_required
```

## P2.4 Campaign Schema

```json
{
  "campaign_id": "uuid",
  "user_id": "uuid",
  "candidate_profile_id": "uuid",
  "natural_language_prompt": "Apply to top US tech companies where I fit",
  "campaign_name": "Top US Technology Companies",
  "structured_query": {
    "target_countries": ["United States"],
    "target_locations": ["Remote", "Global Remote"],
    "company_types": ["AI", "SaaS", "Cloud", "Product"],
    "company_quality": "top_or_high_growth",
    "role_tracks": ["auto_detect"],
    "exclude_roles": [],
    "minimum_fit_score": 75,
    "salary": {
      "minimum_usd": 30000,
      "ideal_usd": 100000
    },
    "include_internal_people": true,
    "include_email_discovery": true,
    "include_cover_letter": true,
    "include_resume_tailoring": true
  },
  "execution_mode": "approval_required",
  "status": "created"
}
```

## P2.5 Database Tables

### campaign_campaigns

Fields: id, user_id, candidate_profile_id, name, natural_language_prompt, structured_query_json, execution_mode, status, created_at, updated_at.

### campaign_constraints

Fields: id, campaign_id, constraint_type, constraint_value, mandatory, created_at.

### campaign_runs

Fields: id, campaign_id, run_type, status, started_at, completed_at, error_json.

## P2.6 APIs

```http
POST /campaigns/create
GET  /campaigns/{campaign_id}
POST /campaigns/{campaign_id}/parse
POST /campaigns/{campaign_id}/run
POST /campaigns/{campaign_id}/pause
POST /campaigns/{campaign_id}/cancel
GET  /campaigns/{campaign_id}/status
```

## P2.7 Events Emitted

```text
CampaignCreated
CampaignParsed
CampaignRunRequested
CampaignPaused
CampaignCancelled
```

## P2.8 Acceptance Criteria

1. Natural language prompt is converted into structured JSON.
2. Output JSON validates against campaign schema.
3. Missing role family can be inferred from Career Vault.
4. Default execution mode is approval_required.
5. Campaign can be run through API without frontend.

---

# P3. Job Discovery Engine

## P3.1 Purpose

Job Discovery finds jobs from allowed sources and normalizes them into a single internal schema.

## P3.2 Sources

Allowed MVP sources:

1. ATS job boards:
   - Greenhouse
   - Lever
   - Ashby
   - Workable
   - BambooHR, if connector exists
2. Job APIs:
   - Adzuna or equivalent
   - SerpAPI/Google Jobs equivalent if configured
3. Company career pages.
4. Screenshot-to-job extraction followed by web verification.
5. Manual job URL input.

Not allowed:

1. LinkedIn scraping.
2. LinkedIn auto-scroll automation.
3. LinkedIn auto-message.
4. LinkedIn auto-connect.
5. Random personal-data scraping.

## P3.3 Responsibilities

1. Accept structured campaign query.
2. Search job sources.
3. Retrieve job details.
4. Normalize jobs.
5. Deduplicate jobs.
6. Verify job freshness.
7. Store source metadata.
8. Emit JobsDiscovered and JobNormalized events.

## P3.4 Normalized Job Schema

```json
{
  "job_id": "uuid",
  "company_id": "uuid",
  "source": "greenhouse",
  "source_job_id": "12345",
  "title": "AI Solutions Consultant",
  "company_name": "Example AI Inc",
  "location_text": "Remote - United States",
  "country": "United States",
  "remote_type": "remote",
  "employment_type": "full_time",
  "salary_min": null,
  "salary_max": null,
  "currency": "USD",
  "description": "...",
  "requirements_json": [],
  "responsibilities_json": [],
  "skills_json": [],
  "job_url": "https://...",
  "date_posted": "2026-05-21",
  "date_found": "2026-05-21",
  "status": "normalized",
  "source_confidence": 0.92,
  "content_hash": "sha256"
}
```

## P3.5 Company Schema

```json
{
  "company_id": "uuid",
  "name": "Example AI Inc",
  "website": "https://example.com",
  "industry": "AI/SaaS",
  "company_type": "technology",
  "country": "United States",
  "source_confidence": 0.88,
  "verified": true
}
```

## P3.6 Deduplication Rules

A job is duplicate if:

1. Same company + same title + same location + similar description hash.
2. Same source job ID.
3. Same job URL.
4. Semantic similarity above configured threshold with same company/title.

System must keep the best source record and mark others as duplicates.

## P3.7 Database Tables

### job_companies

Fields: id, name, website, industry, company_type, country, verified, source_confidence, created_at, updated_at.

### job_jobs

Fields: id, company_id, source, source_job_id, title, location_text, country, remote_type, employment_type, salary_min, salary_max, currency, description, requirements_json, responsibilities_json, skills_json, job_url, date_posted, date_found, status, source_confidence, content_hash, created_at, updated_at.

### job_sources

Fields: id, source_name, source_type, base_url, enabled, config_json, created_at.

### job_duplicates

Fields: id, canonical_job_id, duplicate_job_id, match_reason, similarity_score, created_at.

## P3.8 APIs

```http
POST /jobs/discover
GET  /jobs/{job_id}
GET  /jobs?campaign_id={campaign_id}
POST /jobs/{job_id}/refresh
POST /jobs/manual-url
POST /jobs/screenshot/extract
POST /jobs/screenshot/verify
```

## P3.9 Events Emitted

```text
JobDiscoveryStarted
JobsDiscovered
JobNormalized
DuplicateJobDetected
JobExpired
JobVerified
```

## P3.10 Events Consumed

```text
CampaignRunRequested
CampaignParsed
ScreenshotUploaded
```

## P3.11 Acceptance Criteria

1. Campaign can trigger job discovery.
2. Jobs from multiple sources are normalized to one schema.
3. Duplicate jobs are detected.
4. Each job stores original source and URL.
5. LinkedIn is never scraped or automated.
6. Screenshot input is used only for extraction and verification, not blind application.

---

# P4. Job Fit Scoring Engine

## P4.1 Purpose

Fit Scoring determines whether a job is worth pursuing and why.

## P4.2 Responsibilities

1. Parse job description.
2. Extract required skills.
3. Compare job to Career Vault.
4. Score role alignment.
5. Score skill match.
6. Score seniority match.
7. Score remote/location match.
8. Score salary/business value.
9. Identify missing skills.
10. Identify risk flags.
11. Return A/B/C/reject decision.
12. Explain score.

## P4.3 Score Formula

Default scoring weights:

| Component | Weight |
|---|---:|
| Role match | 25 |
| Skill match | 25 |
| Experience/seniority match | 15 |
| Remote/location match | 15 |
| Salary/business value | 10 |
| Company quality | 5 |
| Internal outreach potential | 5 |
| Total | 100 |

## P4.4 Decision Thresholds

| Fit Score | Decision |
|---:|---|
| 85-100 | A-grade: generate application package and people discovery |
| 70-84 | B-grade: prepare for review if campaign has capacity |
| 55-69 | Save for later; no package generation by default |
| Below 55 | Reject |

## P4.5 Score Output Schema

```json
{
  "job_score_id": "uuid",
  "job_id": "uuid",
  "candidate_profile_id": "uuid",
  "fit_score": 84,
  "decision": "prepare_application",
  "component_scores": {
    "role_match": 22,
    "skill_match": 20,
    "seniority_match": 12,
    "location_match": 15,
    "salary_business_value": 8,
    "company_quality": 4,
    "internal_outreach_potential": 3
  },
  "matched_skills": ["AI automation", "consulting", "LMS"],
  "missing_skills": ["Salesforce"],
  "risk_flags": ["US work authorization unclear"],
  "explanation": "Strong role match due to AI consulting and learning technology experience.",
  "confidence": 0.82
}
```

## P4.6 Database Tables

### score_job_scores

Fields: id, job_id, candidate_profile_id, campaign_id, fit_score, decision, component_scores_json, matched_skills_json, missing_skills_json, risk_flags_json, explanation, confidence, prompt_version, model_name, created_at.

### score_rules

Fields: id, rule_key, rule_name, rule_json, enabled, created_at.

### score_evaluations

Fields: id, job_score_id, evaluator_type, evaluation_result_json, created_at.

## P4.7 APIs

```http
POST /jobs/{job_id}/score
POST /campaigns/{campaign_id}/score-jobs
GET  /jobs/{job_id}/score
GET  /campaigns/{campaign_id}/scores
POST /scores/{score_id}/override
```

## P4.8 Events Emitted

```text
JobScoringStarted
JobScored
JobRejectedByScore
ApplicationRecommended
ManualScoreReviewRequired
```

## P4.9 Acceptance Criteria

1. Every discovered job can be scored.
2. Score contains numeric score and explanation.
3. Missing skills are identified.
4. Risk flags are identified.
5. Decision thresholds are applied.
6. User/admin can override score.
7. All scoring outputs are stored for audit.

---

# P5. Resume and Letter Generator

## P5.1 Purpose

This module generates job-specific application assets based only on approved Career Vault facts.

## P5.2 Outputs

For each approved/recommended job, generate:

1. Tailored resume.
2. Cover letter.
3. Role-fit summary.
4. Resume change log.
5. ATS keyword alignment note.
6. Unsupported-claim report.
7. Optional DOCX/PDF files.

## P5.3 Hard Rules

The module must never invent:

- Companies.
- Job titles.
- Degrees.
- Certifications.
- Years of experience.
- Revenue numbers.
- Client names.
- Tools not approved in Career Vault.
- Skills in do-not-claim list.

## P5.4 Application Package Schema

```json
{
  "application_package_id": "uuid",
  "job_id": "uuid",
  "candidate_profile_id": "uuid",
  "resume_version_id": "uuid",
  "cover_letter_id": "uuid",
  "fit_summary": [
    "Strong AI automation and consulting alignment",
    "Relevant LMS and corporate learning technology background"
  ],
  "unsupported_claims_detected": [],
  "risk_flags": ["Salesforce mentioned in JD but not in approved claims"],
  "status": "review_pending"
}
```

## P5.5 Resume Change Log Schema

```json
{
  "resume_version_id": "uuid",
  "changes": [
    {
      "section": "Summary",
      "change_type": "reordered",
      "description": "Moved AI automation and consulting experience to the first sentence."
    },
    {
      "section": "Skills",
      "change_type": "keyword_alignment",
      "description": "Added approved skill 'AI workflow automation' because it exists in Career Vault."
    }
  ],
  "unsupported_claims_detected": []
}
```

## P5.6 Database Tables

### package_application_packages

Fields: id, job_id, campaign_id, candidate_profile_id, status, fit_summary_json, unsupported_claims_json, risk_flags_json, created_at, updated_at.

### doc_resume_versions

Fields: id, application_package_id, candidate_profile_id, version_number, resume_text, docx_url, pdf_url, change_log_json, status, created_at.

### doc_cover_letters

Fields: id, application_package_id, letter_text, docx_url, pdf_url, status, created_at.

### doc_generation_logs

Fields: id, application_package_id, generation_type, prompt_version, model_name, input_hash, output_hash, created_at.

## P5.7 APIs

```http
POST /jobs/{job_id}/generate-package
GET  /application-packages/{package_id}
GET  /application-packages/{package_id}/resume
GET  /application-packages/{package_id}/cover-letter
POST /application-packages/{package_id}/regenerate
POST /application-packages/{package_id}/validate-claims
```

## P5.8 Events Emitted

```text
ApplicationPackageGenerationStarted
ApplicationPackageCreated
ResumeVersionCreated
CoverLetterCreated
UnsupportedClaimDetected
ApplicationPackageRequiresReview
```

## P5.9 Acceptance Criteria

1. A-grade job can generate application package.
2. Resume uses only approved claims.
3. Cover letter is job-specific.
4. Change log is created.
5. Unsupported claims block approval.
6. Package status becomes review_pending.

---

# P6. People Finder / Internal Access Engine

## P6.1 Purpose

The People Finder identifies the best internal people to contact for a job: hiring managers, recruiters, talent partners, internal referrers, and business leaders.

## P6.2 Responsibilities

1. Verify company identity.
2. Understand likely department/team for the job.
3. Search for public professional profiles/pages.
4. Identify recruiter/hiring manager/referrer candidates.
5. Rank people by relevance.
6. Generate contact candidates.
7. Pass email candidates to Email Discovery/Verification.
8. Store source URLs and confidence.
9. Respect do-not-contact rules.

## P6.3 Person Types

| Person Type | Priority | Description |
|---|---:|---|
| likely_hiring_manager | Highest | Person likely owning the role/team |
| recruiter | Highest | Talent acquisition person handling role/company |
| internal_referrer | Medium | Employee who may refer or route candidate |
| business_leader | Medium | Useful for senior/startup roles |
| irrelevant | Reject | Person not useful for outreach |

## P6.4 Ranking Factors

| Factor | Weight |
|---|---:|
| Same department as job | 25 |
| Hiring-related title | 20 |
| Company match | 20 |
| Location match | 10 |
| Seniority relevance | 10 |
| Public professional contact availability | 10 |
| Recent/verified source | 5 |

## P6.5 Person Schema

```json
{
  "person_id": "uuid",
  "company_id": "uuid",
  "name": "Jane Doe",
  "title": "Director of AI Solutions",
  "person_type": "likely_hiring_manager",
  "source_url": "https://example.com/team/jane",
  "source_type": "company_page/public_web",
  "email": null,
  "email_verification_status": "not_checked",
  "confidence": 0.78,
  "why_relevant": "Owns AI Solutions team aligned with job title.",
  "do_not_contact": false
}
```

## P6.6 Database Tables

### people_people

Fields: id, company_id, name, title, person_type, source_url, source_type, email, phone, confidence, why_relevant, do_not_contact, created_at, updated_at.

### people_person_sources

Fields: id, person_id, source_url, source_type, extracted_text, confidence, created_at.

### people_rankings

Fields: id, job_id, person_id, rank_position, relevance_score, ranking_reason, created_at.

## P6.7 APIs

```http
POST /jobs/{job_id}/find-people
GET  /jobs/{job_id}/people
GET  /companies/{company_id}/people
POST /people/{person_id}/mark-do-not-contact
POST /people/{person_id}/update
```

## P6.8 Events Emitted

```text
PeopleDiscoveryStarted
PersonCandidateFound
PeopleRanked
PeopleFound
DoNotContactAdded
```

## P6.9 Acceptance Criteria

1. For A-grade job, People Finder returns ranked contact candidates.
2. Each person has source URL.
3. Each person has reason for relevance.
4. Do-not-contact person is excluded from outreach.
5. No LinkedIn scraping is performed.
6. Unverified email is not treated as ready-to-send.

---

# P7. Outreach Generator

## P7.1 Purpose

The Outreach Generator creates personalized job outreach drafts for recruiters, hiring managers, internal referrers, and follow-ups.

## P7.2 Draft Types

1. Recruiter email.
2. Hiring manager email.
3. Internal referrer message.
4. LinkedIn manual message text.
5. Follow-up email.
6. Call script.
7. Short fit summary.

## P7.3 Rules

1. Do not send messages directly.
2. Do not create email draft unless recipient is verified or manually approved.
3. Include truthful fit summary only.
4. Do not overstate relationship.
5. Do not imply referral exists if it does not.
6. Do not mass-personalize spam.
7. Keep first outreach short.

## P7.4 Outreach Draft Schema

```json
{
  "outreach_draft_id": "uuid",
  "application_package_id": "uuid",
  "person_id": "uuid",
  "channel": "email",
  "draft_type": "hiring_manager_email",
  "subject": "Application for AI Solutions Consultant role",
  "body": "Hi Jane,...",
  "personalization_points": [
    "Role aligns with AI automation and consulting background",
    "Company is hiring for AI Solutions team"
  ],
  "status": "review_pending"
}
```

## P7.5 Database Tables

### outreach_drafts

Fields: id, application_package_id, person_id, channel, draft_type, subject, body, personalization_points_json, gmail_draft_id, status, created_at, updated_at.

### outreach_templates

Fields: id, template_key, template_name, channel, draft_type, template_body, active, created_at.

### outreach_followups

Fields: id, outreach_draft_id, followup_number, scheduled_for, subject, body, status, created_at.

## P7.6 APIs

```http
POST /application-packages/{package_id}/generate-outreach
GET  /application-packages/{package_id}/outreach-drafts
POST /outreach-drafts/{draft_id}/regenerate
POST /outreach-drafts/{draft_id}/approve
POST /outreach-drafts/{draft_id}/reject
POST /outreach-drafts/{draft_id}/create-gmail-draft
```

## P7.7 Events Emitted

```text
OutreachGenerationStarted
OutreachDraftCreated
OutreachDraftRequiresReview
GmailDraftRequested
```

## P7.8 Acceptance Criteria

1. System creates separate draft for recruiter and hiring manager.
2. Draft explains role-specific fit.
3. Draft does not contain unsupported claims.
4. Draft status is review_pending by default.
5. Gmail draft creation is blocked if recipient email is unverified.

---

# P8. Review and Approval Queue

## P8.1 Purpose

The Review Queue is the human approval layer. Nothing is sent or submitted without approval.

## P8.2 Reviewable Items

1. Tailored resume.
2. Cover letter.
3. Recruiter email.
4. Hiring manager email.
5. Referral message.
6. Call script.
7. Job application submission.
8. Follow-up email.

## P8.3 Review Statuses

```text
pending_review
approved
rejected
needs_edit
edited
expired
blocked_by_policy
```

## P8.4 Approval Object Schema

```json
{
  "review_id": "uuid",
  "user_id": "uuid",
  "entity_type": "outreach_draft",
  "entity_id": "uuid",
  "status": "pending_review",
  "requested_at": "timestamp",
  "reviewed_at": null,
  "review_notes": null
}
```

## P8.5 Database Tables

### review_items

Fields: id, user_id, entity_type, entity_id, status, requested_at, reviewed_at, review_notes, created_at.

### review_decisions

Fields: id, review_item_id, decision, notes, actor_user_id, created_at.

## P8.6 APIs

```http
GET  /review-queue
GET  /review-queue/{review_id}
POST /review-queue/{review_id}/approve
POST /review-queue/{review_id}/reject
POST /review-queue/{review_id}/needs-edit
POST /review-queue/{review_id}/update-content
```

## P8.7 Events Emitted

```text
ReviewRequested
UserApproved
UserRejected
UserRequestedEdit
ReviewExpired
```

## P8.8 Acceptance Criteria

1. Every outgoing action creates a review item.
2. System blocks sending until approval exists.
3. User can approve, reject, or request edit.
4. Approval history is stored.
5. Workers cannot bypass review queue.

---

# P9. Application Tracker / Job CRM

## P9.1 Purpose

The Tracker records job pipeline status, outreach status, follow-ups, interviews, rejections, and notes.

## P9.2 Pipeline Stages

```text
found
scored
recommended
package_created
people_found
outreach_drafted
review_pending
applied
outreach_sent
followup_due
interviewing
offer
rejected
closed
archived
```

## P9.3 Tracker Event Schema

```json
{
  "tracker_event_id": "uuid",
  "job_id": "uuid",
  "campaign_id": "uuid",
  "event_type": "outreach_draft_created",
  "notes": "Hiring manager draft created",
  "created_at": "timestamp"
}
```

## P9.4 Database Tables

### tracker_applications

Fields: id, job_id, campaign_id, candidate_profile_id, status, applied_at, last_contacted_at, next_followup_at, notes, created_at, updated_at.

### tracker_events

Fields: id, application_id, job_id, campaign_id, event_type, notes, metadata_json, created_at.

### tracker_followups

Fields: id, application_id, due_date, followup_type, status, notes, created_at.

## P9.5 APIs

```http
GET  /tracker/applications
GET  /tracker/applications/{application_id}
POST /tracker/applications/{application_id}/status
POST /tracker/applications/{application_id}/notes
POST /tracker/applications/{application_id}/followup
GET  /tracker/followups/due
```

## P9.6 Events Emitted

```text
ApplicationTrackerCreated
ApplicationStatusUpdated
FollowupScheduled
FollowupDue
ApplicationClosed
```

## P9.7 Acceptance Criteria

1. Every recommended job gets tracker record.
2. Status updates are stored.
3. Follow-up dates can be scheduled.
4. Follow-up due list is available.
5. Historical event timeline is visible through API.

---

# P10. Optional Email Discovery Module

## P10.1 Purpose

Email Discovery generates possible professional email candidates and verifies them through the user’s email verification API.

## P10.2 Responsibilities

1. Generate professional email candidates from name and company domain.
2. Parse company contact pages.
3. Use known email patterns if available.
4. Call user-provided verification API.
5. Store verification result.
6. Block outreach if email is invalid/unverified.
7. Store source URLs and confidence.

## P10.3 Non-Responsibilities

The module must not:

1. Scrape personal emails from non-professional sources.
2. Use unverified emails for sending.
3. Send emails.
4. Bypass do-not-contact list.

## P10.4 Email Candidate Schema

```json
{
  "email_candidate_id": "uuid",
  "person_id": "uuid",
  "email": "jane.doe@example.com",
  "generation_method": "pattern_first_last",
  "source_domain": "example.com",
  "verification_status": "verified",
  "verification_score": 0.95,
  "verified_at": "timestamp"
}
```

## P10.5 APIs

```http
POST /email-discovery/people/{person_id}/generate
POST /email-discovery/candidates/{candidate_id}/verify
GET  /email-discovery/people/{person_id}/candidates
```

## P10.6 Acceptance Criteria

1. Email candidates are generated only for professional domains.
2. Verification API is called.
3. Invalid emails are not used in outreach.
4. Verification source and timestamp are stored.
5. Do-not-contact emails are blocked.

---

# P11. Optional Autonomous Browsing Sandbox

## P11.1 Purpose

Autonomous Browsing supports controlled browser-based research and form prefill experiments on allowed domains only.

## P11.2 Allowed Uses

1. Company career pages.
2. Public company websites.
3. ATS job forms where automation is allowed.
4. User-owned/internal dashboards.
5. Screenshot-based extraction.
6. Form prefill before human submission.

## P11.3 Disallowed Uses

1. LinkedIn scraping.
2. LinkedIn auto-message.
3. LinkedIn auto-connect.
4. LinkedIn profile scraping.
5. Blind form submission.
6. Personal-data scraping.
7. Bypassing bot protections.
8. Any site disallowed by configuration.

## P11.4 Required Controls

1. Domain allowlist.
2. Action logging.
3. Human approval gate before submission.
4. Screenshot capture for audit.
5. Session timeout.
6. Error handling.
7. Compliance check before action.

## P11.5 Database Tables

### browser_sessions

Fields: id, user_id, campaign_id, allowed_domain, status, started_at, ended_at, error_json.

### browser_actions

Fields: id, browser_session_id, action_type, selector, url, screenshot_url, status, created_at.

## P11.6 APIs

```http
POST /browser/session/start
POST /browser/session/{session_id}/navigate
POST /browser/session/{session_id}/extract
POST /browser/session/{session_id}/prefill
POST /browser/session/{session_id}/stop
GET  /browser/session/{session_id}/actions
```

## P11.7 Acceptance Criteria

1. Browser automation runs only on allowlisted domains.
2. Every action is logged.
3. Submission is blocked without approval.
4. LinkedIn domains are blocked by default.
5. Browser session can be stopped safely.

---

## 11. Global Event Catalog

The system must support the following event types.

```text
UserCreated
ResumeUploaded
ResumeParsed
CareerProfileCreated
CareerProfileUpdated
CampaignCreated
CampaignParsed
CampaignRunRequested
JobDiscoveryStarted
JobsDiscovered
JobNormalized
DuplicateJobDetected
JobVerified
JobScoringStarted
JobScored
JobRejectedByScore
ApplicationRecommended
ApplicationPackageGenerationStarted
ApplicationPackageCreated
ResumeVersionCreated
CoverLetterCreated
UnsupportedClaimDetected
PeopleDiscoveryStarted
PersonCandidateFound
PeopleRanked
PeopleFound
EmailCandidateGenerated
EmailVerified
EmailRejected
OutreachGenerationStarted
OutreachDraftCreated
ReviewRequested
UserApproved
UserRejected
GmailDraftCreated
ApplicationTrackerCreated
ApplicationStatusUpdated
FollowupScheduled
FollowupDue
DoNotContactAdded
WorkflowFailed
WorkflowPaused
WorkflowResumed
```

---

## 12. API Design Requirements

### 12.1 API Principles

1. RESTful API for MVP.
2. JSON request/response.
3. UUID primary IDs.
4. Every endpoint returns trace_id.
5. Every mutation creates audit log.
6. Long-running actions return job/workflow ID.
7. Errors must be structured.

### 12.2 Error Response Schema

```json
{
  "error": {
    "code": "UNSUPPORTED_CLAIM_DETECTED",
    "message": "The generated resume included a claim not approved in the Career Vault.",
    "details": {},
    "trace_id": "uuid"
  }
}
```

### 12.3 Core MVP Endpoints

```http
POST /career-vault/resume/upload
POST /campaigns/create
POST /campaigns/{campaign_id}/run
GET  /campaigns/{campaign_id}/status
GET  /campaigns/{campaign_id}/jobs
POST /jobs/{job_id}/score
POST /jobs/{job_id}/generate-package
POST /jobs/{job_id}/find-people
POST /application-packages/{package_id}/generate-outreach
GET  /review-queue
POST /review-queue/{review_id}/approve
POST /outreach-drafts/{draft_id}/create-gmail-draft
GET  /tracker/applications
```

---

## 13. Database Design Summary

The developer must create migrations for all tables listed in module sections.

### 13.1 Required Database Capabilities

1. PostgreSQL.
2. UUID keys.
3. JSONB fields.
4. Created/updated timestamps.
5. Soft deletion where needed.
6. Audit logs.
7. Foreign key consistency.
8. Table namespaces/prefixes per module.

### 13.2 Sensitive Data Handling

Sensitive fields:

- Resume files.
- Resume text.
- Email addresses.
- Phone numbers.
- Outreach body.
- Career story.
- Salary target.

Requirements:

1. Encrypt sensitive data at rest where possible.
2. Restrict access by user_id.
3. Do not log raw resume text in application logs.
4. Do not expose private data in trace logs unless redacted.
5. Store source URLs for public contact discovery.

---

## 14. Prompt and AI Output Requirements

### 14.1 Prompt Versioning

Every AI prompt must have:

1. Prompt key.
2. Version number.
3. Module owner.
4. Input schema.
5. Output schema.
6. Test cases.
7. Evaluation examples.

### 14.2 Required Prompts

```text
parse_resume.md
parse_campaign.md
extract_job_requirements.md
score_job_fit.md
tailor_resume.md
generate_cover_letter.md
find_people_ranking.md
generate_recruiter_email.md
generate_hiring_manager_email.md
generate_referral_message.md
generate_call_script.md
validate_unsupported_claims.md
```

### 14.3 AI Output Validation

All critical LLM outputs must be validated with Pydantic schemas.

Critical outputs:

1. Campaign structured query.
2. Parsed resume object.
3. Job score object.
4. Resume change log.
5. Unsupported claim report.
6. People ranking.
7. Outreach draft metadata.

If validation fails:

1. Retry once with correction prompt.
2. If still invalid, mark as manual_review_required.
3. Store invalid output for debugging with redaction.

---

## 15. Compliance and Safety Requirements

### 15.1 LinkedIn Rule

The system must not automate LinkedIn scraping, LinkedIn connecting, LinkedIn messaging, or LinkedIn profile extraction.

Allowed:

- User-provided LinkedIn screenshot as input.
- Manual message text generation.
- Search instructions for user to manually use.

Disallowed:

- Automated browser interaction on LinkedIn.
- Profile scraping.
- Auto-connect.
- Auto-message.
- Data extraction extensions.

### 15.2 Email Outreach Rules

1. No mass spam.
2. No misleading subject lines.
3. No fake relationship claims.
4. No unverified recipient email unless manually approved.
5. Do-not-contact must be honored.
6. User must approve before sending.
7. Store source for every contact.

### 15.3 Resume Integrity Rules

1. Use only Career Vault approved claims.
2. Do not create fake skills.
3. Do not create fake companies.
4. Do not exaggerate numbers.
5. Unsupported claims must block approval.

### 15.4 Browser Automation Rules

1. Use allowlist.
2. Log all actions.
3. Stop before final submit.
4. Respect site restrictions.
5. Do not bypass CAPTCHA or anti-bot protections.

---

## 16. Observability and Evaluation

### 16.1 Observability Requirements

System must track:

1. Workflow duration.
2. Module success/failure rate.
3. LLM prompt version.
4. LLM model used.
5. Token/cost estimate.
6. Job scoring distributions.
7. Unsupported claim rates.
8. Email verification rates.
9. Draft approval/rejection rates.
10. Follow-up outcomes.

### 16.2 Evaluation Datasets

Create evaluation sets for:

1. Resume parsing.
2. Campaign parsing.
3. Job scoring.
4. Resume tailoring.
5. Unsupported claim detection.
6. People ranking.
7. Outreach writing.

### 16.3 Quality Metrics

| Metric | Target |
|---|---:|
| Campaign parse valid JSON rate | > 98% |
| Resume parse usable profile rate | > 90% |
| Job normalization success | > 95% |
| Duplicate detection precision | > 90% |
| Unsupported claim detection | > 95% for known test cases |
| Email draft approval rate | To be measured |
| False high-fit job rate | < 20% after tuning |

---

## 17. Testing Requirements

### 17.1 Unit Tests

Each module must have unit tests for:

1. Schema validation.
2. Business rules.
3. Error handling.
4. Event emission.
5. Database service methods.

### 17.2 Integration Tests

Required integration tests:

1. Resume upload -> Career Vault created.
2. Campaign prompt -> structured campaign.
3. Campaign -> jobs discovered.
4. Jobs -> scored.
5. A-grade job -> application package.
6. Application package -> people found.
7. People -> outreach drafts.
8. Draft -> review queue.
9. Approval -> Gmail draft.
10. Tracker updated.

### 17.3 End-to-End MVP Test

Test input:

```text
Apply to top technology companies across the USA where I am fit.
```

Expected backend output:

1. Campaign created.
2. Structured query created.
3. Jobs discovered.
4. Jobs scored.
5. A-grade jobs selected.
6. Application packages generated.
7. People discovered.
8. Outreach drafts generated.
9. Review queue populated.
10. Tracker records created.

### 17.4 Security Tests

1. LinkedIn domain blocked in autonomous browsing.
2. Unverified email blocks Gmail draft.
3. Unsupported resume claim blocks approval.
4. Do-not-contact blocks outreach.
5. Cross-user data access blocked.

---

## 18. Deployment Requirements

### 18.1 MVP Deployment

MVP can be deployed with:

```text
FastAPI backend
PostgreSQL
Qdrant
Redis if needed
Worker process
Object storage / local storage
Langfuse or equivalent
```

### 18.2 Environment Variables

Required:

```text
DATABASE_URL
QDRANT_URL
QDRANT_API_KEY
OPENAI_API_KEY or selected LLM provider key
EMAIL_VERIFICATION_API_KEY
GMAIL_CLIENT_ID
GMAIL_CLIENT_SECRET
GMAIL_REDIRECT_URI
OBJECT_STORAGE_BUCKET
LANGFUSE_PUBLIC_KEY
LANGFUSE_SECRET_KEY
APP_ENV
```

### 18.3 Local Development

Developer must be able to run:

```bash
docker compose up
```

Then access:

```text
FastAPI docs: http://localhost:8000/docs
PostgreSQL: localhost
Qdrant: localhost
Worker logs: terminal/docker logs
```

---

## 19. Recommended Repository Structure

```text
job-copilot-platform/
│
├── apps/
│   └── backend/
│       ├── app/
│       │   ├── main.py
│       │   ├── config.py
│       │   ├── database.py
│       │   ├── core_kernel/
│       │   │   ├── module_registry.py
│       │   │   ├── workflow_engine.py
│       │   │   ├── event_bus.py
│       │   │   ├── audit_service.py
│       │   │   └── permissions.py
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
│       │   │   ├── schemas/
│       │   │   ├── prompts/
│       │   │   ├── observability/
│       │   │   └── utils/
│       │   └── tests/
│       ├── migrations/
│       ├── docker-compose.yml
│       ├── pyproject.toml
│       └── README.md
│
├── docs/
│   ├── srs/
│   ├── architecture/
│   ├── api-contracts/
│   ├── module-specs/
│   └── decision-records/
│
└── packages/
    ├── shared-contracts/
    ├── shared-prompts/
    └── shared-evals/
```

---

## 20. Build Phases

## Phase 1: Backend Foundation

Build:

1. FastAPI app.
2. PostgreSQL connection.
3. Module registry.
4. Audit logs.
5. User model.
6. Basic health endpoints.
7. Docker Compose.

Acceptance:

- API boots locally.
- Database migrations run.
- Module registry works.
- Audit log can write entries.

## Phase 2: Career Vault

Build:

1. Resume upload.
2. Resume parsing.
3. Career profile creation.
4. Skills and claims.
5. Do-not-claim list.

Acceptance:

- Resume upload creates structured profile.
- Approved claims can be queried.

## Phase 3: Campaign Planner

Build:

1. Natural language campaign creation.
2. Structured campaign parser.
3. Campaign run status.

Acceptance:

- “Apply to top US tech companies where I fit” becomes valid JSON campaign.

## Phase 4: Job Discovery

Build:

1. Greenhouse/Lever/Ashby/Workable connector wrappers.
2. Job normalization.
3. Deduplication.
4. Manual job URL.

Acceptance:

- Campaign can discover and store jobs.

## Phase 5: Fit Scoring

Build:

1. Rule scoring.
2. Embedding similarity.
3. LLM explanation.
4. Decision thresholds.

Acceptance:

- Jobs get A/B/C/reject decisions.

## Phase 6: Application Package Generation

Build:

1. Resume tailoring.
2. Cover letter.
3. Change log.
4. Unsupported claim detection.

Acceptance:

- A-grade job generates reviewable application package.

## Phase 7: People Finder and Email Verification

Build:

1. Company verification.
2. People discovery.
3. Person ranking.
4. Email candidate generation.
5. Email verification API adapter.

Acceptance:

- A-grade job gets ranked people and verified emails where possible.

## Phase 8: Outreach and Review Queue

Build:

1. Recruiter email.
2. Hiring manager email.
3. Referral message.
4. Call script.
5. Review queue.

Acceptance:

- Drafts are created and blocked pending approval.

## Phase 9: Gmail Drafts and Tracker

Build:

1. Gmail draft creation.
2. Tracker records.
3. Follow-up scheduling.

Acceptance:

- Approved draft becomes Gmail draft.
- Tracker status updates.

## Phase 10: Optional Browsing Sandbox

Build:

1. Allowlisted Playwright sessions.
2. Screenshot extraction.
3. Form prefill.
4. Action logging.

Acceptance:

- Browser session can extract data from allowed site and cannot run on LinkedIn.

---

## 21. MVP Success Definition

MVP is successful when the backend can perform this complete scenario through API/Postman:

```text
Input:
User uploads resume.
User says: “Apply to top technology companies across the USA where I am fit.”

Expected Output:
1. Career Vault created.
2. Campaign parsed.
3. Jobs discovered.
4. Jobs normalized and deduplicated.
5. Jobs scored.
6. A-grade jobs selected.
7. Tailored resume and cover letter generated.
8. Recruiter/hiring manager/referrer candidates found.
9. Email candidates verified using configured API.
10. Outreach drafts created.
11. Review queue populated.
12. Gmail draft created only after approval.
13. Tracker records all steps.
```

---

## 22. Non-Functional Requirements

### 22.1 Performance

| Operation | Target |
|---|---:|
| Resume upload parse | < 60 seconds for typical resume |
| Campaign parse | < 15 seconds |
| Job normalization | < 2 seconds per job |
| Job scoring | < 30 seconds per job initially |
| Application package generation | < 90 seconds per job |
| People discovery | < 120 seconds per job initially |

### 22.2 Reliability

1. Failed module task must be retryable.
2. Workflow must not restart from beginning if one job fails.
3. Each job should be processed independently after discovery.
4. Partial campaign completion is acceptable.

### 22.3 Scalability

Initial target:

- 1 user.
- 10 campaigns.
- 1,000 discovered jobs.
- 100 scored jobs per campaign.
- 20 application packages per campaign.

Future target:

- Multi-user.
- 100,000+ jobs.
- Multiple workers.

### 22.4 Security

1. User data isolation.
2. API authentication.
3. Redacted logs.
4. Secrets in environment variables.
5. No raw API keys in code.
6. Sensitive files stored securely.

---

## 23. Developer Implementation Rules

1. Do not build frontend in MVP.
2. Use API-first development.
3. Every module must have tests.
4. Every LLM output must have schema validation.
5. Every external call must be wrapped in adapter class.
6. Every external source must store source URL.
7. Every outgoing action must check review status.
8. Do not scrape LinkedIn.
9. Do not auto-send emails.
10. Do not invent resume claims.
11. Do not let modules directly access each other’s private internals.
12. Do not hardcode user-specific values except in seed/test data.

---

## 24. Reference Architecture Notes

The architecture is based on the following principles:

1. **Modular monolith first:** faster development while boundaries are still stabilizing.
2. **Contract-first modules:** each section can later become a separate product.
3. **Central orchestration:** campaign flow needs a controller.
4. **Event-driven extensibility:** modules emit events so future features can subscribe.
5. **Human-in-the-loop:** critical actions pause for review.
6. **Validated AI outputs:** no free-form AI response should control backend flow.
7. **Auditability:** every important action is logged.
8. **Compliance-by-design:** no LinkedIn scraping, no blind outreach, no unsupported claims.

---

## 25. External References and Notes

The developer should review these sources before implementation:

1. FastAPI documentation and releases: https://github.com/fastapi/fastapi/releases
2. LangGraph durable execution and human-in-the-loop concepts: https://docs.langchain.com/oss/python/langgraph/durable-execution
3. PydanticAI structured output documentation: https://ai.pydantic.dev/output/
4. Docling GitHub repository: https://github.com/docling-project/docling
5. Qdrant payload and filtering documentation: https://qdrant.tech/documentation/concepts/payload/
6. Gmail API draft creation: https://developers.google.com/gmail/api/reference/rest/v1/users.drafts/create
7. LinkedIn prohibited software policy: https://www.linkedin.com/help/linkedin/answer/a1341387/prohibited-software-and-extensions
8. FTC CAN-SPAM compliance guide: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business
9. AWS guidance on orchestration and choreography: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-integrating-microservices/choosing-approach.html
10. AWS guidance on decomposing monoliths into microservices: https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/welcome.html

---

## 26. SRS 2.0 Repository Strategy

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

## 27. Final Developer Checklist

Before starting development, the developer must confirm:

```text
[ ] I understand that this is backend-first.
[ ] I understand that Product 0 is the core orchestration kernel.
[ ] I understand each product module must be independently replaceable.
[ ] I understand no LinkedIn scraping is allowed.
[ ] I understand no blind auto-apply is allowed.
[ ] I understand email sending requires approval.
[ ] I understand resume claims must come from Career Vault.
[ ] I understand every AI output must be schema-validated.
[ ] I understand every module must emit events.
[ ] I understand every external source must be logged.
[ ] I understand optional email discovery is separate.
[ ] I understand optional autonomous browsing is sandboxed.
```

---

# End of SRS
