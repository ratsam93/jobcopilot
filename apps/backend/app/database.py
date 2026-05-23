from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


@dataclass
class DatabaseConfig:
    url: str | None = None


def build_database_config(database_url: str | None) -> DatabaseConfig:
    return DatabaseConfig(url=database_url)


def build_engine(database_url: str | None) -> Engine | None:
    if not database_url:
        return None
    return create_engine(database_url, pool_pre_ping=True, future=True)


def check_database(database_url: str | None) -> bool:
    engine = build_engine(database_url)
    if engine is None:
        return False
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False
