"""
Auth router — registration, JWT login, password reset/verification
(fastapi-users), plus a small /auth/me endpoint kept for frontend
compatibility with the previous Appwrite-based response shape.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.core.dependencies import CurrentUser
from app.core.security import auth_backend, fastapi_users
from app.schemas.auth import UserCreate, UserInfo, UserRead, UserUpdate

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)

router.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/jwt")
router.include_router(fastapi_users.get_register_router(UserRead, UserCreate))
router.include_router(fastapi_users.get_reset_password_router())
router.include_router(fastapi_users.get_verify_router(UserRead))
router.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users")


@router.get("/me", response_model=UserInfo)
async def get_me(user: CurrentUser):
    """Return the current authenticated user's basic info."""
    return UserInfo(id=user.id, email=user.email, name=user.name)
