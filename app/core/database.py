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

A third table, ``users``, holds authentication accounts (see
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
from sqlalchemy import Column, DateTime, Index, Integer, String, create_engine
from sqlalchemy.dialects.postgresql import JSONB
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
