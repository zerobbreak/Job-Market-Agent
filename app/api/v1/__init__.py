"""
V1 API router aggregator.

Collects all v1 routers under a single ``/api/v1`` prefix.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    profiles,
    jobs,
    applications,
    analytics,
    files,
    admin,
)

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth.router)
v1_router.include_router(profiles.router)
v1_router.include_router(jobs.router)
v1_router.include_router(applications.router)
v1_router.include_router(analytics.router)
v1_router.include_router(files.router)
v1_router.include_router(admin.router)
