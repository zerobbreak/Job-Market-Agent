"""
Application-related Pydantic schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class ApplicationStatusUpdate(BaseModel):
    """Request body for updating application status."""

    status: str = Field(..., pattern="^(pending|applied|interview|rejected)$")


# ── Responses ─────────────────────────────────────────────────────────────────

class ApplicationResponse(BaseModel):
    """Single application in API response."""

    id: str
    jobTitle: str = "Unknown Position"
    company: str = "Unknown Company"
    jobUrl: str = ""
    location: str = ""
    status: str = "applied"
    appliedDate: str = ""
    files: Optional[Any] = None


class ApplicationListResponse(BaseModel):
    """Paginated list of applications."""

    success: bool = True
    applications: List[ApplicationResponse] = []
    page: int = 1
    limit: int = 10
    total: int = 0
