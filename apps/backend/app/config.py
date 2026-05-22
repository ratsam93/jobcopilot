from pydantic import BaseModel


class Settings(BaseModel):
    app_env: str = "development"
    database_url: str | None = None
    qdrant_url: str | None = None


settings = Settings()

