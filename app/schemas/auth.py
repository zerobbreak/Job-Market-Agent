"""
Auth-related Pydantic schemas.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi_users import schemas
from pydantic import BaseModel


class UserRead(schemas.BaseUser[uuid.UUID]):
    """fastapi-users read schema — adds the app's custom `name` field."""

    name: str = ""


class UserCreate(schemas.BaseUserCreate):
    """fastapi-users registration schema."""

    name: str = ""


class UserUpdate(schemas.BaseUserUpdate):
    """fastapi-users update schema."""

    name: Optional[str] = None


class UserInfo(BaseModel):
    """Public-facing user information (kept for /auth/me compatibility)."""

    id: str
    email: str = ""
    name: str = ""
