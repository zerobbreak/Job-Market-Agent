"""
Job-related Pydantic schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class JobSearchRequest(BaseModel):
    """Request body for job search."""

    query: str = Field(..., min_length=2, max_length=200, description="Job search query")
    location: str = Field(default="South Africa", max_length=100)
    max_results: int = Field(default=20, ge=1, le=100)
    use_cache: bool = True


class JobMatchRequest(BaseModel):
    """Request body for triggering fresh job matching."""

    force_refresh: bool = False
    location: str = Field(default="South Africa", max_length=100)
    max_results: int = Field(default=20, ge=1, le=100)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


class JobFeedbackRequest(BaseModel):
    """User feedback on a job match (save, apply, hide, dismiss)."""

    job_id: str
    action: str = Field(..., pattern="^(save|apply|hide|dismiss)$")
    rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)


class ApplyPreviewRequest(BaseModel):
    """Request to start preview document generation for a job."""

    job: Dict[str, Any]
    template_type: str = Field(default="modern", pattern="^(modern|minimalist|academic)$")


# ── Responses ─────────────────────────────────────────────────────────────────

class JobResponse(BaseModel):
    """Single job in API response."""

    id: Optional[str] = None
    title: str = ""
    company: str = ""
    location: str = ""
    url: str = ""
    description: str = ""
    source: str = ""
    date_posted: Optional[str] = None
    job_type: Optional[str] = None

    # Enhanced fields from jobspy 1.1.82
    is_remote: Optional[bool] = None
    company_url: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    company_industry: Optional[str] = None
    job_level: Optional[str] = None
    job_function: Optional[str] = None
    country: Optional[str] = None
    emails: List[str] = []
    skills: List[str] = []

    # Computed fields
    match_score: Optional[float] = None
    relevance_score: Optional[float] = None

    model_config = {"extra": "allow"}


class JobSearchResponse(BaseModel):
    """Response from job search endpoint."""

    success: bool = True
    jobs: List[JobResponse] = []
    total: int = 0
    cached: bool = False


class JobMatchResponse(BaseModel):
    """Response from job matching endpoint."""

    success: bool = True
    matches: List[Dict[str, Any]] = []
    total: int = 0
    cached: bool = False


class PreviewStatusResponse(BaseModel):
    """Status of a preview generation job."""

    success: bool = True
    status: str = "unknown"
    progress: int = 0
    phase: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
