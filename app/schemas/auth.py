"""
Auth-related Pydantic schemas.
"""

from __future__ import annotations

from pydantic import BaseModel


class OTPResponse(BaseModel):
    """Response from OTP generation endpoint."""

    success: bool = True
    token: str


class UserInfo(BaseModel):
    """Public-facing user information."""

    id: str
    email: str = ""
    name: str = ""
