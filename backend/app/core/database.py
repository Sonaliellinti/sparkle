"""
Database engine & session management.

Design note — Postgres/Supabase portability:
    The ONLY database-specific branch in this whole project is the
    `connect_args` line below, which SQLite needs and Postgres does not.
    Everything else (models, queries, sessions) is plain SQLAlchemy and
    works unchanged against Postgres once DATABASE_URL is switched in
    the environment/.env file.
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# SQLite requires this flag for multi-threaded FastAPI access; Postgres does not.
_connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,  # gracefully recovers dropped connections (important for hosted Postgres)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def get_db() -> Generator:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope():
    """Context-manager version of get_db, for use outside request handlers
    (e.g. scripts, seed data, background jobs)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
