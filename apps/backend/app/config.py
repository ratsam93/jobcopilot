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
    )


settings = load_settings()
