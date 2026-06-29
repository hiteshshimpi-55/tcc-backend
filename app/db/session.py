from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache
def get_engine():
    settings = get_settings()
    return create_engine(settings.sqlalchemy_database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory():
    return sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def run_migrations() -> None:
    import structlog
    from alembic.config import Config

    from alembic import command

    logger = structlog.get_logger(__name__)
    alembic_cfg = Config("alembic.ini")
    try:
        command.upgrade(alembic_cfg, "head")
    except Exception:
        logger.exception("database_migration_failed")
        raise
