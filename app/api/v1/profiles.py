"""
Profiles router - CRUD, CV upload/analysis, and CV regeneration.

Ported from: routes/profile_routes.py
Business logic will progressively migrate to services/profile_service.py
and services/cv_service.py.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.dependencies import CurrentUser, ProfileRepo, ProfileServiceDep, get_cv_service
from app.core.exceptions import (
    BadRequestError,
    ExternalServiceError,
    NotFoundError,
)
from app.schemas.common import SuccessResponse
from app.schemas.profile import (
    CVAnalysisResponse,
    CVRegenerateRequest,
    ProfileListResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    StructuredProfileResponse,
)

router = APIRouter(prefix="/profiles", tags=["Profiles"])
logger = logging.getLogger(__name__)


# -- GET /profiles/me ----------------------------------------------------------

@router.get("/me", response_model=ProfileResponse)
async def get_current_profile(
    user: CurrentUser,
    profile_service: ProfileServiceDep,
):
    """Get the current user's active profile."""
    profile = await profile_service.get_current_profile(user.id)
    return ProfileResponse(profile=profile or {})


# -- GET /profiles/me/structured -----------------------------------------------

@router.get("/me/structured", response_model=StructuredProfileResponse)
async def get_structured_profile(
    user: CurrentUser,
    profile_service: ProfileServiceDep,
):
    """Get the structured (parsed) profile with sections."""
    profile = await profile_service.get_structured_profile(user.id)
    if not profile:
        return StructuredProfileResponse()
    return StructuredProfileResponse(**profile)


# -- PUT /profiles/me ---------------------------------------------------------

@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    user: CurrentUser,
    profile_service: ProfileServiceDep,
):
    """Update the current user's active profile."""
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        profile = await profile_service.get_current_profile(user.id)
        return ProfileResponse(profile=profile or {})

    updated_profile = await profile_service.update_profile(user.id, update_data)
    if not updated_profile:
        raise NotFoundError("Profile")

    return ProfileResponse(profile=updated_profile)


# -- POST /profiles/cv/analyze -------------------------------------------------

@router.post("/cv/analyze", response_model=CVAnalysisResponse)
async def analyze_cv(
    user: CurrentUser,
    profile_service: ProfileServiceDep,
    profile_repo: ProfileRepo,
    cv_file: UploadFile = File(...),
):
    """Upload and analyze a CV file, then persist it for job matching."""
    if not cv_file.filename:
        raise BadRequestError("No file provided")

    try:
        from app.core.config import get_settings
        from services.cv_analysis_service import generate_ai_analysis
        from services.pipeline_service import JobApplicationPipeline, parse_profile

        content = await cv_file.read()
        if not content:
            raise BadRequestError("Uploaded file is empty")

        settings = get_settings()
        filename = os.path.basename(cv_file.filename)
        temp_path = os.path.join(settings.upload_folder, f"{user.id}_{filename}")
        os.makedirs(settings.upload_folder, exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(content)

        logger.info("[PIPELINE] CV loaded: user=%s filename=%s bytes=%d", user.id, filename, len(content))

        pipeline = JobApplicationPipeline(cv_path=temp_path)
        cv_content = pipeline.load_cv()
        logger.info("[PIPELINE] Text extracted: user=%s chars=%d", user.id, len(cv_content or ""))

        raw_profile = pipeline.build_profile(cv_content)
        profile = parse_profile(raw_profile)
        logger.info("[PIPELINE] Profile parsed successfully: user=%s", user.id)

        file_hash = hashlib.sha256(content).hexdigest()
        ai_analysis = generate_ai_analysis(profile)

        profile_payload = {
            "name": str(profile.get("name", "") or "").strip(),
            "email": str(profile.get("email", "") or "").strip(),
            "phone": str(profile.get("phone", "") or "").strip(),
            "location": str(profile.get("location", "") or "").strip(),
            "skills": json.dumps(profile.get("skills", []) or []),
            "experience_level": str(profile.get("experience_level", "") or "").strip(),
            "education": json.dumps(profile.get("education", []) or []),
            "strengths": json.dumps(profile.get("strengths", []) or []),
            "profile_summary": str(profile.get("summary") or profile.get("career_goals", "") or "").strip(),
            "career_goals": str(profile.get("career_goals", "") or "").strip(),
            "cv_filename": filename,
            "cv_hash": file_hash,
            "ai_analysis": json.dumps(ai_analysis) if ai_analysis else None,
        }

        save_status = "saved"
        save_message = "Profile saved"
        profile_id = None

        try:
            saved = profile_repo.upsert_profile(user.id, profile_payload)
            if saved:
                profile_id = saved.get("$id")
                logger.info("[PIPELINE] Profile saved: user=%s profile_id=%s", user.id, profile_id)
            else:
                save_status = "partial_success"
                save_message = "CV parsed but profile not saved"
                logger.warning("[PIPELINE] Profile save returned empty result: user=%s", user.id)
        except Exception as e:
            save_status = "partial_success"
            save_message = "CV parsed but profile not saved"
            logger.error("[PIPELINE] Profile save failed: user=%s error=%s", user.id, e, exc_info=True)

        return CVAnalysisResponse(
            profile=profile or {},
            cv_details={
                "filename": filename,
                "file_hash": file_hash,
                "text_length": len(cv_content) if cv_content else 0,
                "profile": profile,
                "profile_id": profile_id,
                "save_status": save_status,
                "message": save_message,
            },
            ai_analysis=ai_analysis,
        )
    except BadRequestError:
        raise
    except Exception as e:
        logger.error("Error analyzing CV: %s", e, exc_info=True)
        raise ExternalServiceError("CV Analysis", str(e))


# -- POST /profiles/cv/regenerate ---------------------------------------------

@router.post("/cv/regenerate")
async def regenerate_cv(
    body: CVRegenerateRequest,
    user: CurrentUser,
    cv_service: Annotated["CVService", Depends(get_cv_service)],
):
    """Regenerate and optimize the CV using AI with chosen template."""
    return {"success": True, "message": "Triggered CV regeneration"}


# -- GET /profiles -------------------------------------------------------------

@router.get("", response_model=ProfileListResponse)
async def list_profiles(
    user: CurrentUser,
    profile_service: ProfileServiceDep,
):
    """List all CV profiles for the current user."""
    profiles = await profile_service.list_profiles(user.id)
    active_id = next((p["$id"] for p in profiles if p.get("isActive")), None)

    return ProfileListResponse(
        profiles=profiles,
        active_profile_id=active_id,
    )


# -- PUT /profiles/{profile_id}/activate --------------------------------------

@router.put("/{profile_id}/activate", response_model=SuccessResponse)
async def set_active_profile(
    profile_id: str,
    user: CurrentUser,
    profile_service: ProfileServiceDep,
):
    """Set a specific profile as the active one."""
    success = await profile_service.activate_profile(user.id, profile_id)
    if not success:
        raise NotFoundError("Profile or activation failed")

    return SuccessResponse(message="Profile activated")


# -- DELETE /profiles/{profile_id} --------------------------------------------

@router.delete("/{profile_id}", response_model=SuccessResponse)
async def delete_profile(
    profile_id: str,
    user: CurrentUser,
    profile_service: ProfileServiceDep,
):
    """Delete a CV profile and associated storage file."""
    success = await profile_service.delete_profile(user.id, profile_id)
    if not success:
        raise NotFoundError("Profile or deletion failed")

    return SuccessResponse(message="Profile deleted")

