"""
Jobs router — search, matching, preview, and application automation.

Ported from: routes/job_routes.py
Business logic delegates to services; this file is HTTP-only.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends

from app.core.config import Settings, get_settings
from app.core.dependencies import CurrentUser, JobServiceDep, CVServiceDep, MatchRepo, JobRepo
from app.core.exceptions import ExternalServiceError, NotFoundError
from app.schemas.common import SuccessResponse
from app.schemas.job import (
    JobSearchResponse,
    JobSearchRequest,
    JobMatchResponse,
    JobMatchRequest,
    JobFeedbackRequest,
    PreviewStatusResponse,
    ApplyPreviewRequest
)

router = APIRouter(prefix="/jobs", tags=["Jobs"])
logger = logging.getLogger(__name__)


# ── Search ────────────────────────────────────────────────────────────────────

@router.post("/search", response_model=JobSearchResponse)
async def search_jobs(
    body: JobSearchRequest,
    user: CurrentUser,
    job_service: JobServiceDep,
):
    """Search for jobs using jobspy scraper."""
    # This currently still uses the legacy pipeline inside JobService
    result = await job_service.search_and_match(user.id, body)
    if not result.get("success"):
        raise ExternalServiceError("Job Search", result.get("error", "Unknown error"))
    
    return JobSearchResponse(
        jobs=result.get("matches", []),
        total=result.get("total_matches", 0),
        cached=False,
    )


# ── Matching ──────────────────────────────────────────────────────────────────

@router.get("/matches", response_model=JobMatchResponse)
async def get_cached_matches(user: CurrentUser, match_repo: MatchRepo):
    """Get cached job matches for the current user."""
    doc = match_repo.get_user_matches(user.id)
    if not doc:
        return JobMatchResponse(matches=[], total=0, cached=True)
    
    matches = match_repo._deserialize(doc.get("matches", "[]"))
    match_repo.update_last_seen(doc["$id"])
    
    return JobMatchResponse(
        matches=matches,
        total=len(matches),
        cached=True,
    )


@router.post("/matches", response_model=JobMatchResponse)
async def get_or_refresh_matches(
    body: JobMatchRequest,
    user: CurrentUser,
    job_service: JobServiceDep,
    match_repo: MatchRepo,
    background_tasks: BackgroundTasks,
):
    """
    Get job matches. If force_refresh is True, triggers fresh matching.
    """
    if not body.force_refresh:
        return await get_cached_matches(user, match_repo)

    # For now, we'll keep it synchronous in the service or move to background
    # But to match the schema and frontend expectations:
    result = await job_service.search_and_match(user.id, JobSearchRequest(
        location=body.location,
        max_results=body.max_results,
        use_cache=False
    ))
    
    if result.get("success") and result.get("matches"):
        match_repo.cache_matches(user.id, body.location or "South Africa", result["matches"])

    return JobMatchResponse(
        matches=result.get("matches", []),
        total=result.get("total_matches", 0),
        cached=False,
    )


# ── Feedback ──────────────────────────────────────────────────────────────────

@router.post("/feedback", response_model=SuccessResponse)
async def submit_feedback(body: JobFeedbackRequest, user: CurrentUser, match_repo: MatchRepo):
    """Submit user feedback on a job match."""
    # Logic to record feedback for future training
    logger.info("Feedback received: User=%s, Job=%s, Action=%s", user.id, body.job_id, body.action)
    return SuccessResponse()


# ── Apply Preview ─────────────────────────────────────────────────────────────

@router.post("/apply-preview", response_model=PreviewStatusResponse)
async def start_apply_preview(
    body: ApplyPreviewRequest,
    user: CurrentUser,
    cv_service: CVServiceDep,
    background_tasks: BackgroundTasks,
):
    """Start preview document generation (CV + cover letter) for a job."""
    import hashlib
    job_key = f"{body.job.get('title', '')}-{body.job.get('company', '')}-{user.id}"
    job_id = hashlib.md5(job_key.encode()).hexdigest()

    # Get profile data for tailoring
    from app.repositories.profile_repo import ProfileRepository
    from app.core.dependencies import get_profile_repo, get_settings
    
    # We need profile repo but it's not injected here. We can use specialized injection or just get it.
    # Actually, we should probably have ProfileService handle this.
    
    # For now, assuming cv_service can get what it needs or we pass it
    # We'll need the raw CV text which is in the profile
    
    # Trigger background task
    # background_tasks.add_task(cv_service.generate_preview, ...)
    
    return PreviewStatusResponse(
        status="initializing",
        progress=0,
        phase="Starting preview generation",
    )


@router.get("/apply-preview/{job_id}/status", response_model=PreviewStatusResponse)
async def get_preview_status(job_id: str, user: CurrentUser, job_repo: JobRepo):
    """Get status of a preview generation job."""
    state = job_repo.get(job_id)
    if not state:
        raise NotFoundError("Preview job")

    return PreviewStatusResponse(
        status=state.get("status", "unknown"),
        progress=state.get("progress", 0),
        phase=state.get("phase"),
        error=state.get("error"),
        result=state.get("result") if state.get("status") == "done" else None,
    )
