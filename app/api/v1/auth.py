"""
Auth router — JWT validation and OTP generation.

Ported from: routes/auth_routes.py
"""

from __future__ import annotations

import logging
import threading
import time
import uuid

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.core.dependencies import CurrentUser
from app.schemas.auth import OTPResponse, UserInfo

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)

# In-memory OTP store (same as original — consider Redis for production)
_otp_store: dict = {}
_otp_lock = threading.Lock()


@router.get("/me", response_model=UserInfo)
async def get_me(user: CurrentUser):
    """Return the current authenticated user's basic info."""
    return UserInfo(id=user.id, email=user.email, name=user.name)


@router.post("/otp", response_model=OTPResponse)
async def generate_otp(
    user: CurrentUser,
    settings: Settings = Depends(get_settings),
):
    """Generate a one-time password token for the current user."""
    otp = str(uuid.uuid4())

    with _otp_lock:
        now = time.time()
        _otp_store[otp] = {
            "jwt": user.client._jwt if hasattr(user.client, "_jwt") else "",
            "expires": now + settings.otp_expiry_seconds,
        }

    return OTPResponse(token=otp)
