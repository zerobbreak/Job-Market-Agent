"""
SQLAlchemy engine/session and models for Postgres.

The backend used to store all application data in Appwrite's schemaless
TablesDB, then moved wholesale into a single generic ``documents`` table
(one JSON blob per collection) to avoid a field-by-field migration. That
table still exists and still backs the ``analytics`` collection, but the
four collections with real query/filter/sort needs each now have their own
typed table instead:

- ``profiles``, ``jobs`` (preview-generation state), ``matches`` (one row
  per user/job pair, denormalized — scraped postings aren't persisted as
  their own entity), and ``applications``. Fields the app actually
  filters, sorts, or joins on are real indexed columns with foreign keys
  into ``users``/``files``; anything else lives in a per-row ``attrs``
  JSONB catch-all.
- ``documents``: the remaining collection-scoped JSON document store
  (``analytics``, and any future ad-hoc collection), unchanged.
- ``files``: metadata for files stored on the local/volume filesystem
  (see ``app.repositories.storage_repo``).

Every repository still returns the flat, Appwrite-shaped dict (``$id`` /
``$createdAt`` / ``$updatedAt``) regardless of which table backs it, via
``PostgresRepository``/``TypedRepository`` in ``app.repositories.postgres_base``
— so existing service/router code didn't need to change.

A further table, ``users``, holds authentication accounts (see
``app.core.security``) — it's a normal typed table (not a JSON document)
since fastapi-users queries directly on ``email``.

Usage::

    from app.core.database import get_session, init_db

    init_db()  # idempotent — creates tables if missing
    with get_session() as session:
        ...

fastapi-users requires an async session; ``get_async_session`` provides one
against the same database, independent of the sync engine used everywhere
else in the app.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import AsyncGenerator

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
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


class User(SQLAlchemyBaseUserTableUUID, Base):
    """Authentication account (fastapi-users). Adds ``id``, ``email``,
    ``hashed_password``, ``is_active``, ``is_superuser``, ``is_verified``."""

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")


class Profile(Base):
    """A user's CV-derived profile. Multiple profiles per user are allowed
    (one per CV upload); ``is_active`` marks the one currently in use."""

    __tablename__ = "profiles"

    id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(PGUUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(320), nullable=True)
    phone = Column(String(64), nullable=True)
    location = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    experience_level = Column(String(100), nullable=True)
    education = Column(String(500), nullable=True)
    career_goals = Column(Text, nullable=True)
    cv_filename = Column(String(500), nullable=True)
    cv_file_id = Column(String(64), ForeignKey("files.id", ondelete="SET NULL"), nullable=True)
    cv_hash = Column(String(128), nullable=True)
    has_cv = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    notification_enabled = Column(Boolean, nullable=False, default=False)
    notification_threshold = Column(Integer, nullable=False, default=70)
    attrs = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class Job(Base):
    """State for a CV/cover-letter preview generation job. Scraped job
    postings themselves aren't persisted — they're matched and returned
    directly by ``JobService.search_and_match`` without being stored."""

    __tablename__ = "jobs"

    id = Column(String(64), primary_key=True)
    user_id = Column(PGUUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="initializing", index=True)
    progress = Column(Integer, nullable=False, default=0)
    phase = Column(String(255), nullable=True)
    template_type = Column(String(50), nullable=False, default="modern")
    error = Column(Text, nullable=True)
    attrs = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class Match(Base):
    """One row per (user, matched job) pair, replacing the old single
    JSON blob of every match for a user. Job details are denormalized
    onto the row since scraped postings have no table of their own."""

    __tablename__ = "matches"

    id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(PGUUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_hash = Column(String(500), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    match_score = Column(Float, nullable=True, index=True)
    semantic_score = Column(Float, nullable=True)
    keyword_score = Column(Float, nullable=True)
    score_breakdown = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    match_reasons = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    attrs = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "job_hash", name="uq_matches_user_job"),
    )


class Application(Base):
    """A tracked job application, with generated CV/cover-letter file links."""

    __tablename__ = "applications"

    id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(PGUUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company = Column(String(255), nullable=True)
    role = Column(String(255), nullable=True)
    job_url = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="generated", index=True)
    match_score = Column(Float, nullable=True)
    ats_score = Column(Float, nullable=True)
    cv_storage_id = Column(String(64), ForeignKey("files.id", ondelete="SET NULL"), nullable=True)
    cover_letter_storage_id = Column(String(64), ForeignKey("files.id", ondelete="SET NULL"), nullable=True)
    job_description = Column(Text, nullable=True)
    views = Column(Integer, nullable=False, default=0)
    # App-managed ISO-string timestamps (distinct from created_at/updated_at)
    # kept as-is: existing code sorts/reads these by name directly.
    date_created = Column(String(64), nullable=True, index=True)
    date_updated = Column(String(64), nullable=True)
    attrs = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


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


def _async_database_url(url: str) -> str:
    """Swap in an async driver for the same connection string."""
    if "+asyncpg" in url or "+aiosqlite" in url:
        return url
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return url


@lru_cache
def get_async_engine():
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it in the environment/.env file."
        )
    return create_async_engine(_async_database_url(settings.database_url), pool_pre_ping=True, future=True)


@lru_cache
def get_async_session_factory() -> async_sessionmaker:
    return async_sessionmaker(bind=get_async_engine(), expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: an async session, used by fastapi-users."""
    async with get_async_session_factory()() as session:
        yield session
