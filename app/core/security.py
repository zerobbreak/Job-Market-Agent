"""
JWT authentication via Appwrite — FastAPI dependency injection.

Replaces the Flask ``@login_required`` decorator and ``flask.g`` pattern
with a clean ``Depends(get_current_user)`` approach.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

# FastAPI security scheme — extracts "Bearer <token>" automatically
_bearer_scheme = HTTPBearer(auto_error=True)


# ── Authenticated user container ─────────────────────────────────────────────

@dataclass
class AuthenticatedUser:
    """Holds the validated Appwrite user identity + a scoped client."""

    id: str
    email: str = ""
    name: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)
    _client: Any = field(default=None, repr=False)

    @property
    def client(self):
        """Appwrite Client scoped to this user's JWT."""
        return self._client


# ── Dependency ────────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    """
    FastAPI dependency that validates an Appwrite JWT.

    Usage in routers::

        @router.get("/me")
        async def get_profile(user: AuthenticatedUser = Depends(get_current_user)):
            ...
    """
    token = credentials.credentials

    try:
        from appwrite.client import Client
        from appwrite.services.account import Account

        client = Client()
        client.set_endpoint(settings.appwrite_api_endpoint)
        client.set_project(settings.appwrite_project_id)
        client.set_jwt(token)

        account = Account(client)
        user_data = account.get()

        return AuthenticatedUser(
            id=user_data["$id"],
            email=user_data.get("email", ""),
            name=user_data.get("name", ""),
            raw=user_data,
            _client=client,
        )
    except Exception as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser | None:
    """
    Like ``get_current_user`` but returns ``None`` instead of 401
    when no token is provided. Useful for public endpoints that
    optionally personalize responses for logged-in users.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]

    try:
        from appwrite.client import Client
        from appwrite.services.account import Account

        client = Client()
        client.set_endpoint(settings.appwrite_api_endpoint)
        client.set_project(settings.appwrite_project_id)
        client.set_jwt(token)

        account = Account(client)
        user_data = account.get()

        return AuthenticatedUser(
            id=user_data["$id"],
            email=user_data.get("email", ""),
            name=user_data.get("name", ""),
            raw=user_data,
            _client=client,
        )
    except Exception:
        return None
