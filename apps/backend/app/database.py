from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    url: str | None = None


def build_database_config(database_url: str | None) -> DatabaseConfig:
    return DatabaseConfig(url=database_url)

