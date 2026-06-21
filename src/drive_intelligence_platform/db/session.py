"""Database session factory and engine helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from drive_intelligence_platform.core.config import AppSettings
from drive_intelligence_platform.db.base import Base


def initialize_database(settings: AppSettings) -> Engine:
    """Create the database engine and ensure all known tables exist."""

    engine = create_db_engine(settings)
    Base.metadata.create_all(engine)
    return engine


def create_db_engine(settings: AppSettings) -> Engine:
    """Create a SQLAlchemy engine."""

    return create_engine(settings.database_url, future=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a session factory bound to an engine."""

    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """Yield a database session and close it when done."""

    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()