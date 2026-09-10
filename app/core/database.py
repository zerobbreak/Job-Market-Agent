"""
SQLAlchemy engine/session and generic document-store models for Postgres.

The backend used to store all application data in Appwrite's schemaless
TablesDB. To keep that same "flexible document" shape (and avoid a
field-by-field migration for every attribute a service happens to write),
data now lives in two tables:

- ``documents``: a collection-scoped JSON document store. Each row belongs
  to a named collection (jobs / applications / profiles / matches /
  analytics) and carries its attributes in a JSON column, mirroring the
  Appwrite row shape (``$id`` / ``$createdAt`` / ``$updatedAt``) at the
  repository layer so existing service/router code didn't need to change.
- ``files``: metadata for files stored on the local/volume filesystem
  (see ``app.repositories.storage_repo``).

Usage::

    from app.core.database import get_session, init_db

    init_db()  # idempotent — creates tables if missing
    with get_session() as session:
        ...
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from functools import lru_cache

from sqlalchemy import Column, DateTime, Index, Integer, String, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import JSON

from app.core.config import get_settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Document(Base):
    """A single collection-scoped document (Appwrite-row equivalent)."""

    __tablename__ = "documents"

    collection = Column(String(64), primary_key=True)
    id = Column(String(255), primary_key=True)
    user_id = Column(String(255), nullable=True)
    data = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        Index("ix_documents_collection_user_id", "collection", "user_id"),
    )


class FileAsset(Base):
    """Metadata for a file stored on the local/volume filesystem."""

    __tablename__ = "files"

    id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    namespace = Column(String(64), nullable=False, default="files")
    filename = Column(String(500), nullable=False)
    relative_path = Column(String(1000), nullable=False)
    content_type = Column(String(255), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


@lru_cache
def get_engine():
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it in the environment/.env file."
        )
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


@lru_cache
def get_session_factory() -> sessionmaker:
    return sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)


def get_session() -> Session:
    """Open a new short-lived session — use as a context manager."""
    return get_session_factory()()


def init_db() -> None:
    """Create tables if they don't exist yet (idempotent, dev/bootstrap use).

    For controlled schema changes in production, use the Alembic migrations
    under ``migrations/`` instead (``alembic upgrade head``).
    """
    Base.metadata.create_all(get_engine())
