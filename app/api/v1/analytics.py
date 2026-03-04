"""
Analytics router — event tracking, engagement analytics, and heatmaps.

Ported from: routes/analytics_routes.py
"""

from __future__ import annotations

import json
import logging

from appwrite.id import ID
from appwrite.services.tables_db import TablesDB
from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.core.dependencies import CurrentUser
from app.core.exceptions import BadRequestError, ExternalServiceError
from app.schemas.analytics import (
    EngagementAnalyticsResponse,
    HeatmapResponse,
    TrackEventRequest,
    TrackViewRequest,
    UpdateAnalyticsStatusRequest,
)
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)


@router.post("", response_model=SuccessResponse)
async def track_event(
    body: TrackEventRequest,
    user: CurrentUser,
    settings: Settings = Depends(get_settings),
):
    """Record an analytics event."""
    try:
        tables_db = TablesDB(user.client)
        tables_db.create_row(
            settings.appwrite_db_id,
            settings.collection_id_analytics,
            ID.unique(),
            data={
                "userId": user.id,
                "event": body.event,
                "properties": json.dumps(body.properties),
                "page": body.page or "",
            },
        )
        return SuccessResponse()
    except Exception as e:
        logger.error("Error tracking event: %s", e)
        raise ExternalServiceError("Appwrite", str(e))


@router.get("/engagement", response_model=EngagementAnalyticsResponse)
async def get_engagement_analytics(
    user: CurrentUser,
    days: int = 30,
):
    """Get engagement analytics over a period."""
    try:
        # Import here to avoid circular imports during migration
        from services.job_store import get_engagement_analytics as _get_engagement

        analytics = _get_engagement(days=days)
        return EngagementAnalyticsResponse(analytics=analytics)
    except Exception as e:
        logger.error("Error getting engagement analytics: %s", e)
        raise ExternalServiceError("Analytics", str(e))


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_application_heatmap(user: CurrentUser):
    """Get application activity heatmap data."""
    try:
        from services.job_store import get_application_heatmap as _get_heatmap

        heatmap = _get_heatmap()
        return HeatmapResponse(heatmap=heatmap)
    except Exception as e:
        logger.error("Error getting heatmap: %s", e)
        raise ExternalServiceError("Analytics", str(e))


@router.post("/track-view", response_model=SuccessResponse)
async def track_application_view(body: TrackViewRequest, user: CurrentUser):
    """Track a view on an application."""
    try:
        from services.job_store import track_view

        track_view(body.application_id)
        return SuccessResponse()
    except Exception as e:
        logger.error("Error tracking view: %s", e)
        raise ExternalServiceError("Analytics", str(e))


@router.post("/update-status", response_model=SuccessResponse)
async def update_analytics_status(
    body: UpdateAnalyticsStatusRequest,
    user: CurrentUser,
):
    """Update application status in analytics."""
    try:
        from services.job_store import update_application_status

        update_application_status(body.application_id, body.status, body.additional_data)
        return SuccessResponse()
    except Exception as e:
        logger.error("Error updating status: %s", e)
        raise ExternalServiceError("Analytics", str(e))
