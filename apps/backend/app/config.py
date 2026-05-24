import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_env: str = "development"
    database_url: str = "sqlite:///./jobcopilot.db"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str | None = None
    gmail_oauth_client_id: str | None = None
    gmail_oauth_client_secret: str | None = None
    gmail_oauth_redirect_uri: str | None = None
    jobber_base_url: str = "https://jobber.mihir.ch"
    jobber_sources: str = "ashby:linear,lever:netlify,greenhouse:airbnb"
    browser_automation_enabled: bool = False
    crawlee_enabled: bool = False
    cv_matcher_enabled: bool = False
    reactive_resume_enabled: bool = False
    langgraph_enabled: bool = False
    pydantic_ai_enabled: bool = False
    langfuse_host: str | None = None
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    openresume_enabled: bool = False
    openresume_url: str = "http://open-resume:3000"


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL") or os.getenv("JOBCOPILOT_DATABASE_URL", "sqlite:///./jobcopilot.db")
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        database_url=database_url,
        redis_url=os.getenv("JOBCOPILOT_REDIS_URL", "redis://localhost:6379/0"),
        qdrant_url=os.getenv("JOBCOPILOT_QDRANT_URL"),
        gmail_oauth_client_id=os.getenv("JOBCOPILOT_GMAIL_OAUTH_CLIENT_ID"),
        gmail_oauth_client_secret=os.getenv("JOBCOPILOT_GMAIL_OAUTH_CLIENT_SECRET"),
        gmail_oauth_redirect_uri=os.getenv("JOBCOPILOT_GMAIL_OAUTH_REDIRECT_URI"),
        jobber_base_url=os.getenv("JOBCOPILOT_JOBBER_BASE_URL", "https://jobber.mihir.ch"),
        jobber_sources=os.getenv("JOBCOPILOT_JOBBER_SOURCES", "ashby:linear,lever:netlify,greenhouse:airbnb"),
        browser_automation_enabled=_env_bool("JOBCOPILOT_BROWSER_AUTOMATION_ENABLED"),
        crawlee_enabled=_env_bool("JOBCOPILOT_CRAWLEE_ENABLED"),
        cv_matcher_enabled=_env_bool("JOBCOPILOT_CV_MATCHER_ENABLED"),
        reactive_resume_enabled=_env_bool("JOBCOPILOT_REACTIVE_RESUME_ENABLED"),
        langgraph_enabled=_env_bool("JOBCOPILOT_LANGGRAPH_ENABLED"),
        pydantic_ai_enabled=_env_bool("JOBCOPILOT_PYDANTIC_AI_ENABLED"),
        langfuse_host=os.getenv("JOBCOPILOT_LANGFUSE_HOST"),
        langfuse_public_key=os.getenv("JOBCOPILOT_LANGFUSE_PUBLIC_KEY"),
        langfuse_secret_key=os.getenv("JOBCOPILOT_LANGFUSE_SECRET_KEY"),
        openresume_enabled=_env_bool("JOBCOPILOT_OPENRESUME_ENABLED"),
        openresume_url=os.getenv("JOBCOPILOT_OPENRESUME_URL", "http://open-resume:3000"),
    )


settings = load_settings()
