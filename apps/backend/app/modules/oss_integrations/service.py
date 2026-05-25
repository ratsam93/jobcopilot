from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from apps.backend.app.config import Settings, settings


class OSSIntegrationStatus(BaseModel):
    key: str
    name: str
    repo_url: str
    license: str
    classification: str
    enabled: bool
    production_status: str
    direct_usage: str
    local_clone_present: bool
    config_keys: list[str]
    safety_notes: list[str]
    next_action: str | None = None


class OSSIntegrationRegistry(BaseModel):
    integrations: list[OSSIntegrationStatus]
    active_count: int
    blocked_count: int
    notes: list[str]


def _clone_exists(repo_dir: str) -> bool:
    return Path("research/oss-reference", repo_dir).exists()


def list_oss_integrations(active_settings: Settings = settings) -> OSSIntegrationRegistry:
    langfuse_enabled = bool(
        active_settings.langfuse_host
        and active_settings.langfuse_public_key
        and active_settings.langfuse_secret_key
    )
    openresume_enabled = active_settings.openresume_enabled

    integrations = [
        OSSIntegrationStatus(
            key="jobber",
            name="jobber",
            repo_url="https://github.com/plibither8/jobber",
            license="MIT",
            classification="active_adapter",
            enabled=bool(active_settings.jobber_sources),
            production_status="wired_into_job_discovery",
            direct_usage="The backend calls the Jobber-compatible ATS API for configured Ashby, Lever, and Greenhouse sources.",
            local_clone_present=_clone_exists("jobber"),
            config_keys=["JOBCOPILOT_JOBBER_BASE_URL", "JOBCOPILOT_JOBBER_SOURCES"],
            safety_notes=["Used for ATS/company job source fetching only."],
        ),
        OSSIntegrationStatus(
            key="docling",
            name="Docling",
            repo_url="https://github.com/docling-project/docling",
            license="MIT",
            classification="active_dependency",
            enabled=True,
            production_status="wired_into_resume_parsing",
            direct_usage="The backend imports Docling's DOCX backend directly for uploaded resume extraction before fallback parsers.",
            local_clone_present=_clone_exists("docling"),
            config_keys=[],
            safety_notes=["Runs server-side document extraction only."],
        ),
        OSSIntegrationStatus(
            key="ever-jobs",
            name="Ever Jobs",
            repo_url="https://github.com/ever-jobs/ever-jobs",
            license="MIT",
            classification="adapter_pending",
            enabled=False,
            production_status="source_plugins_under_review",
            direct_usage="Not yet called by production requests; safe ATS/feed plugins can be lifted into adapters next.",
            local_clone_present=_clone_exists("ever-jobs"),
            config_keys=[],
            safety_notes=["LinkedIn, Indeed, random scraping, auto-apply, and auto-message paths remain blocked."],
            next_action="Select the Ever Jobs source plugin to wire first, excluding blocked scraping sources.",
        ),
        OSSIntegrationStatus(
            key="cv-matcher",
            name="CV-Matcher",
            repo_url="https://github.com/eristavi/CV-Matcher",
            license="Apache-2.0",
            classification="optional_service",
            enabled=active_settings.cv_matcher_enabled,
            production_status="vendored_as_separate_service" if active_settings.cv_matcher_enabled else "available_as_optional_profile",
            direct_usage="CV-Matcher is vendored under oss-services/cv-matcher and can run as a separate Streamlit service on host port 3002.",
            local_clone_present=_clone_exists("CV-Matcher"),
            config_keys=["JOBCOPILOT_CV_MATCHER_ENABLED"],
            safety_notes=["Use for resume-vs-JD scoring validation before copying scoring logic into the backend."],
            next_action=None if active_settings.cv_matcher_enabled else "Start with: docker compose --profile oss-cv-matcher up -d --build cv-matcher",
        ),
        OSSIntegrationStatus(
            key="reactive-resume",
            name="Reactive Resume",
            repo_url="https://github.com/AmruthPillai/Reactive-Resume",
            license="MIT",
            classification="optional_service",
            enabled=active_settings.reactive_resume_enabled,
            production_status="available_as_optional_profile",
            direct_usage="Reactive Resume can run as an isolated optional Docker profile on host port 3003 using its own Postgres, Redis, and object storage.",
            local_clone_present=_clone_exists("Reactive-Resume"),
            config_keys=[
                "JOBCOPILOT_REACTIVE_RESUME_ENABLED",
                "JOBCOPILOT_REACTIVE_RESUME_AUTH_SECRET",
                "JOBCOPILOT_REACTIVE_RESUME_ENCRYPTION_SECRET",
            ],
            safety_notes=["Large full-stack app; keep isolated until explicitly promoted."],
            next_action="Start with: docker compose --profile oss-reactive-resume up -d reactive-resume",
        ),
        OSSIntegrationStatus(
            key="open-resume",
            name="OpenResume",
            repo_url="https://github.com/xitanggg/open-resume",
            license="AGPL-3.0 with user-confirmed owner permission",
            classification="approved_optional_service" if openresume_enabled else "license_approved_disabled",
            enabled=openresume_enabled,
            production_status="vendored_as_separate_service" if openresume_enabled else "approved_but_disabled",
            direct_usage=(
                "OpenResume is vendored under oss-services/open-resume and can run as a separate Next service "
                f"at {active_settings.openresume_url}."
            ),
            local_clone_present=Path("research/oss-reference/agpl/open-resume").exists(),
            config_keys=["JOBCOPILOT_OPENRESUME_ENABLED", "JOBCOPILOT_OPENRESUME_URL"],
            safety_notes=[
                "License owner permission was confirmed by the project owner before product use.",
                "The app remains a separated service instead of being mixed into FastAPI internals.",
            ],
            next_action=None if openresume_enabled else "Set JOBCOPILOT_OPENRESUME_ENABLED=true to show it as active.",
        ),
        OSSIntegrationStatus(
            key="browser-use",
            name="browser-use",
            repo_url="https://github.com/browser-use/browser-use",
            license="MIT",
            classification="sandbox_only",
            enabled=active_settings.browser_automation_enabled,
            production_status="disabled_by_default",
            direct_usage="Not used for production application submission; can only be enabled for controlled sandbox navigation.",
            local_clone_present=_clone_exists("browser-use"),
            config_keys=["JOBCOPILOT_BROWSER_AUTOMATION_ENABLED"],
            safety_notes=["LinkedIn scraping, auto-connect, auto-message, and auto-apply are blocked."],
            next_action="Build a sandbox-only browser task runner with allowlisted domains.",
        ),
        OSSIntegrationStatus(
            key="crawlee-python",
            name="Crawlee Python",
            repo_url="https://github.com/apify/crawlee-python",
            license="Apache-2.0",
            classification="optional_adapter",
            enabled=active_settings.crawlee_enabled,
            production_status="disabled_by_default",
            direct_usage="Not yet used on request path; planned for allowed company career page crawling.",
            local_clone_present=_clone_exists("crawlee-python"),
            config_keys=["JOBCOPILOT_CRAWLEE_ENABLED"],
            safety_notes=["Only allowed company career pages and explicit URLs; no forbidden scraping flows."],
            next_action="Add allowlisted career-page crawler adapter.",
        ),
        OSSIntegrationStatus(
            key="langgraph",
            name="LangGraph",
            repo_url="https://github.com/langchain-ai/langgraph",
            license="MIT",
            classification="workflow_engine_pending",
            enabled=active_settings.langgraph_enabled,
            production_status="celery_workflow_currently_active",
            direct_usage="Workflow execution currently uses Celery; LangGraph can replace the orchestration layer when ready.",
            local_clone_present=_clone_exists("langgraph"),
            config_keys=["JOBCOPILOT_LANGGRAPH_ENABLED"],
            safety_notes=["Pin versions before production enablement."],
            next_action="Move campaign step transitions into a LangGraph graph behind a feature flag.",
        ),
        OSSIntegrationStatus(
            key="pydantic-ai",
            name="PydanticAI",
            repo_url="https://github.com/pydantic/pydantic-ai",
            license="MIT",
            classification="structured_ai_pending",
            enabled=active_settings.pydantic_ai_enabled,
            production_status="pydantic_schemas_currently_active",
            direct_usage="Backend validates AI-shaped outputs with Pydantic schemas; PydanticAI provider calls are not enabled yet.",
            local_clone_present=_clone_exists("pydantic-ai"),
            config_keys=["JOBCOPILOT_PYDANTIC_AI_ENABLED"],
            safety_notes=["Provider keys and cost controls required before live LLM calls."],
            next_action="Wrap structured generation calls with PydanticAI once model credentials are configured.",
        ),
        OSSIntegrationStatus(
            key="langfuse",
            name="Langfuse",
            repo_url="https://github.com/langfuse/langfuse",
            license="MIT",
            classification="optional_observability_service",
            enabled=langfuse_enabled,
            production_status="configured" if langfuse_enabled else "available_as_optional_profile",
            direct_usage="Langfuse can run as an isolated optional Docker profile on host port 3004; traces are emitted only after host and API keys are configured.",
            local_clone_present=_clone_exists("langfuse"),
            config_keys=[
                "JOBCOPILOT_LANGFUSE_HOST",
                "JOBCOPILOT_LANGFUSE_PUBLIC_KEY",
                "JOBCOPILOT_LANGFUSE_SECRET_KEY",
                "JOBCOPILOT_LANGFUSE_INIT_USER_EMAIL",
                "JOBCOPILOT_LANGFUSE_INIT_USER_PASSWORD",
            ],
            safety_notes=[
                "Secrets are never returned by the status endpoint.",
                "The full Langfuse stack is heavier than the other OSS services; start it only when testing observability.",
            ],
            next_action=None if langfuse_enabled else "Start with: docker compose --profile oss-langfuse up -d langfuse-web",
        ),
    ]

    return OSSIntegrationRegistry(
        integrations=integrations,
        active_count=sum(1 for item in integrations if item.enabled and not item.classification.startswith("blocked")),
        blocked_count=sum(1 for item in integrations if item.classification == "blocked_license"),
        notes=[
            "Upstream clones stay in research/oss-reference and are not pushed.",
            "Production code uses small adapters/dependencies instead of building inside upstream apps.",
            "Blocked scraping and auto-send/auto-apply flows remain disabled.",
        ],
    )
