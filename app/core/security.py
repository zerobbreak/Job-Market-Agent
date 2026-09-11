"""
Authentication via fastapi-users (JWT bearer), backed by Postgres.

Replaces the earlier Appwrite-JWT validation. Routers/services keep using
``AuthenticatedUser`` (``id`` / ``email`` / ``name``) exactly as before —
``id`` is normalized to a plain string (fastapi-users' native id is a
``uuid.UUID``) so no call site elsewhere in the app needed to change.

No email provider is wired up yet: password-reset and verification tokens
are logged instead of emailed (see ``UserManager`` below) — swap those log
calls for a real send when you pick a provider.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import User, get_async_session

logger = logging.getLogger(__name__)

settings = get_settings()


async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.secret_key
    verification_token_secret = settings.secret_key

    async def on_after_register(self, user: User, request=None) -> None:
        logger.info("User registered: %s", user.id)

    async def on_after_forgot_password(self, user: User, token: str, request=None) -> None:
        logger.info("Password reset requested for user %s. Reset token: %s", user.id, token)

    async def on_after_request_verify(self, user: User, token: str, request=None) -> None:
        logger.info("Verification requested for user %s. Verify token: %s", user.id, token)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="api/v1/auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.secret_key, lifetime_seconds=60 * 60 * 24 * 7)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

_current_active_user = fastapi_users.current_user(active=True)
_current_active_user_optional = fastapi_users.current_user(active=True, optional=True)


# ── Normalized identity used throughout routers/services ────────────────────

@dataclass
class AuthenticatedUser:
    """Holds the validated user identity (``id`` is always a string)."""

    id: str
    email: str = ""
    name: str = ""


async def get_current_user(user: User = Depends(_current_active_user)) -> AuthenticatedUser:
    """FastAPI dependency: the authenticated user (raises 401 if missing/invalid)."""
    return AuthenticatedUser(id=str(user.id), email=user.email, name=user.name or "")


async def get_optional_user(
    user: Optional[User] = Depends(_current_active_user_optional),
) -> Optional[AuthenticatedUser]:
    """Like ``get_current_user`` but returns ``None`` instead of 401 when no token is provided."""
    if user is None:
        return None
    return AuthenticatedUser(id=str(user.id), email=user.email, name=user.name or "")
