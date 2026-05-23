import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_env: str = "development"
    database_url: str = "sqlite:///./jobcopilot.db"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str | None = None


def load_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        database_url=os.getenv("JOBCOPILOT_DATABASE_URL", "sqlite:///./jobcopilot.db"),
        redis_url=os.getenv("JOBCOPILOT_REDIS_URL", "redis://localhost:6379/0"),
        qdrant_url=os.getenv("JOBCOPILOT_QDRANT_URL"),
    )


settings = load_settings()
