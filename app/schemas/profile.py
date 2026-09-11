"""
Profile-related Pydantic schemas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class ProfileUpdateRequest(BaseModel):
    """Request body for updating user profile."""

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    title: Optional[str] = None
    career_goals: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_level: Optional[str] = None
    education: Optional[Any] = None
    work_experience: Optional[Any] = None
    languages: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    preferred_job_types: Optional[List[str]] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    summary: Optional[str] = None

    model_config = {"extra": "allow"}


class CVRegenerateRequest(BaseModel):
    """Request body for CV regeneration."""

    template_type: str = Field(default="modern", pattern="^(modern|minimalist|academic)$")
    target_job: Optional[Dict[str, Any]] = None
    optimization_level: str = Field(default="standard", pattern="^(basic|standard|aggressive)$")


# ── Responses ─────────────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    """Public-facing profile data."""

    success: bool = True
    profile: Dict[str, Any] = {}


class StructuredProfileResponse(BaseModel):
    """Structured profile with parsed sections."""

    success: bool = True
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    skills: List[str] = []
    experience_level: str = ""
    career_goals: str = ""
    education: Any = None
    work_experience: Any = None
    strengths: List[str] = []
    weaknesses: List[str] = []
    languages: List[str] = []


class CVAnalysisResponse(BaseModel):
    """Response from CV analysis endpoint."""

    success: bool = True
    profile: Dict[str, Any] = {}
    cv_details: Dict[str, Any] = {}
    ai_analysis: Optional[Dict[str, Any]] = None


class CVRegenerateResponse(BaseModel):
    """Response from CV regeneration endpoint."""

    success: bool = True
    cv_markdown: str = ""
    header: Dict[str, Any] = {}
    sections: Dict[str, Any] = {}
    ats_score: Optional[int] = None
    template_type: str = "modern"


class ProfileListResponse(BaseModel):
    """List of user profiles."""

    success: bool = True
    profiles: List[Dict[str, Any]] = []
    active_profile_id: Optional[str] = None
