"""
Analytics-related Pydantic schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class TrackEventRequest(BaseModel):
    """Request body for tracking an analytics event."""

    event: str = Field(..., min_length=1, max_length=100)
    properties: Dict[str, Any] = {}
    page: Optional[str] = None


class TrackViewRequest(BaseModel):
    """Request body for tracking an application view."""

    application_id: str


class UpdateAnalyticsStatusRequest(BaseModel):
    """Request body for updating analytics status."""

    application_id: str
    status: str
    additional_data: Dict[str, Any] = {}


# ── Responses ─────────────────────────────────────────────────────────────────

class EngagementAnalyticsResponse(BaseModel):
    """Response from engagement analytics endpoint."""

    success: bool = True
    analytics: Dict[str, Any] = {}


class HeatmapResponse(BaseModel):
    """Response from application heatmap endpoint."""

    success: bool = True
    heatmap: Dict[str, Any] = {}
