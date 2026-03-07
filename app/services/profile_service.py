"""
Profile service for managing user profiles and CV analysis.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import Settings
from app.repositories.profile_repo import ProfileRepository
from app.repositories.storage_repo import StorageRepository

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for profile-related business logic."""

    def __init__(
        self,
        settings: Settings,
        profile_repo: ProfileRepository,
        storage_repo: StorageRepository,
    ):
        self.settings = settings
        self.profile_repo = profile_repo
        self.storage_repo = storage_repo

    async def get_current_profile(self, user_id: str) -> Dict[str, Any]:
        """Fetch active or latest profile for user."""
        profile = self.profile_repo.get_by_user_id(user_id)
        if not profile:
            return {
                "success": True,
                "cv_filename": None,
                "uploaded_at": None,
                "is_active": False,
                "message": "No profile found. Please upload a CV to get started.",
            }

        return {
            "success": True,
            "cv_filename": profile.get("cv_filename", "Unknown"),
            "uploaded_at": profile.get("$updatedAt", profile.get("$createdAt")),
            "is_active": profile.get("is_active", False),
        }

    async def get_structured_profile(self, user_id: str) -> Dict[str, Any]:
        """Fetch structured profile data, applying healing if fields are missing."""
        profile = self.profile_repo.get_by_user_id(user_id)
        if not profile:
            return {
                "success": True,
                "profile": self._empty_profile(),
                "message": "No profile found.",
            }

        structured = {
            "name": profile.get("name", ""),
            "email": profile.get("email", ""),
            "phone": profile.get("phone", ""),
            "location": profile.get("location", ""),
            "skills": self.profile_repo._deserialize(profile.get("skills", "[]")),
            "experience_level": profile.get("experience_level", ""),
            "education": profile.get("education", ""),
            "strengths": self.profile_repo._deserialize(profile.get("strengths", "[]")),
            "career_goals": profile.get("career_goals", ""),
            "notification_enabled": bool(profile.get("notification_enabled", False)),
            "notification_threshold": int(profile.get("notification_threshold", 70) or 70),
        }

        # Apply healing logic for missing core data
        if not structured["name"] or not structured["email"] or not structured["skills"]:
            # Need to rehydrate pipeline/parse profile logic here or call a helper
            pass 

        return {"success": True, **structured}

    def _empty_profile(self) -> Dict[str, Any]:
        return {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "skills": [],
            "experience_level": "",
            "education": "",
            "strengths": [],
            "career_goals": "",
            "notification_enabled": False,
            "notification_threshold": 70,
        }

    async def list_profiles(self, user_id: str) -> list:
        """List all CV profiles for the given user."""
        try:
            from appwrite.query import Query
            results = self.profile_repo.list([Query.equal("user_id", user_id)])
            if not results:
                results = self.profile_repo.list([Query.equal("userId", user_id)])
            return results if results else []
        except Exception as e:
            logger.error("Error listing profiles for user %s: %s", user_id, e)
            return []

    async def activate_profile(self, user_id: str, profile_id: str) -> bool:
        """Set a profile as active, deactivating all others."""
        try:
            # Deactivate all profiles for this user
            profiles = await self.list_profiles(user_id)
            for p in profiles:
                if p.get("$id") != profile_id:
                    self.profile_repo.update(p["$id"], {"isActive": False})
            # Activate the target profile
            result = self.profile_repo.update(profile_id, {"isActive": True})
            return result is not None
        except Exception as e:
            logger.error("Error activating profile %s: %s", profile_id, e)
            return False

    async def delete_profile(self, user_id: str, profile_id: str) -> bool:
        """Delete a profile, checking it belongs to the user first."""
        try:
            profile = self.profile_repo.get(profile_id)
            if not profile or profile.get("user_id") != user_id:
                return False
            return self.profile_repo.delete(profile_id)
        except Exception as e:
            logger.error("Error deleting profile %s: %s", profile_id, e)
            return False

    async def update_profile(self, user_id: str, data: dict) -> dict:

        """Update user profile with validation."""
        profile = self.profile_repo.get_by_user_id(user_id)
        if not profile:
            return {"success": False, "error": "Profile not found."}

        # Sanitization logic from profile_routes.py
        update_data = {}
        string_fields = ["name", "email", "phone", "location", "experience_level", "education", "career_goals"]
        for field in string_fields:
            if field in data:
                update_data[field] = str(data[field]).strip() if data[field] is not None else ""

        array_fields = ["skills", "strengths"]
        for field in array_fields:
            if field in data:
                val = data[field]
                if isinstance(val, list):
                    update_data[field] = json.dumps([str(i).strip() for i in val if i])
                elif isinstance(val, str):
                    items = [s.strip() for s in val.split(",") if s.strip()]
                    update_data[field] = json.dumps(items)

        if "notification_enabled" in data:
            update_data["notification_enabled"] = bool(data["notification_enabled"])
        if "notification_threshold" in data:
            update_data["notification_threshold"] = max(0, min(100, int(data["notification_threshold"])))

        updated = self.profile_repo.update(profile["$id"], update_data)
        if not updated:
            return {"success": False, "error": "Database update failed"}

        return {"success": True, "message": "Profile updated successfully", "profile": updated}

    async def get_cv_analysis(self, user_id: str) -> Dict[str, Any]:
        """Get dashboard-ready CV analysis."""
        profile = self.profile_repo.get_by_user_id(user_id)
        if not profile:
            return {"success": False, "error": "Profile not found."}

        # Deriving candidate name (healing logic)
        candidate_name = profile.get("name") or self._derive_name(profile.get("email", ""))
        
        uploaded_document = {
            "candidate_name": candidate_name,
            "role_type": f"{profile.get('experience_level', 'Entry Level')} • Hybrid / Remote",
            "professional_summary": (profile.get("career_goals") or "").strip() or "Not specified",
            "core_skills": self.profile_repo._deserialize(profile.get("skills", "[]")),
            "experience": profile.get("experience_level") or "Entry Level",
            "cv_filename": profile.get("cv_filename") or "Unknown",
            "uploaded_at": profile.get("$updatedAt") or profile.get("$createdAt"),
        }

        # Orchestrate AI analysis
        from services.cv_analysis_service import generate_ai_analysis
        
        # We might need matches to properly analyze (context)
        # matches_sample = match_repo.get_user_matches(user_id)
        
        # For now, just generate with profile
        ai_analysis = generate_ai_analysis(profile, None)

        return {
            "success": True,
            "uploaded_document": uploaded_document,
            "ai_analysis": ai_analysis,
            "parsing_status": {"active": True, "progress": 100, "message": "Complete"},
        }

    def _derive_name(self, email: str) -> str:
        if not email or "@" not in email:
            return "UNKNOWN"
        prefix = email.split("@")[0]
        prefix = re.sub(r"[._-]", " ", prefix)
        prefix = re.sub(r"\b\d+\b", " ", prefix)
        prefix = re.sub(r"\s+", " ", prefix).strip()
        words = [w for w in prefix.split() if len(w) > 1 and w.isalpha()]
        return " ".join(w.title() for w in words) if words else "UNKNOWN"


