"""
Admin router — system health and management endpoints.

Ported from: routes/admin_routes.py
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.core.dependencies import CurrentUser
from app.schemas.common import DataResponse

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)


@router.get("/system-stats", response_model=DataResponse)
async def get_system_stats(user: CurrentUser):
    """Get system health statistics (task manager status, etc.)."""
    try:
        from services.task_manager import task_manager

        stats = task_manager.get_system_stats()
        return DataResponse(data=stats)
    except Exception as e:
        logger.error("Error getting system stats: %s", e)
        return DataResponse(data={"status": "unavailable", "error": str(e)})
