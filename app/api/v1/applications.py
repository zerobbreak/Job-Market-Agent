"""
Applications router — track and manage job application statuses.

Ported from: routes/application_routes.py
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query as FastApiQuery

from app.core.dependencies import AppServiceDep, CurrentUser
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/applications", tags=["Applications"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_applications(
    user: CurrentUser,
    app_service: AppServiceDep,
    page: int = FastApiQuery(1, ge=1),
    limit: int = FastApiQuery(10, ge=1, le=100),
):
    """List job applications for the current user."""
    return await app_service.list_applications(user.id, page=page, limit=limit)


@router.put("/{application_id}/status", response_model=SuccessResponse)
async def update_application_status(
    application_id: str,
    body: Dict[str, Any],
    user: CurrentUser,
    app_service: AppServiceDep,
):
    """Update the status of a specific application."""
    new_status = body.get("status")
    if not new_status:
        raise BadRequestError("Missing status")

    success, error = await app_service.update_status(user.id, application_id, new_status)
    if not success:
        if error == "Forbidden":
            raise ForbiddenError()
        if error == "Application not found":
            raise NotFoundError("Application")
        raise BadRequestError(error or "Status update failed")

    return SuccessResponse(message=f"Status updated to {new_status}")
