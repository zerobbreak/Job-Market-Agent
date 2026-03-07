"""
Profile repository for managing user profiles.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from appwrite.client import Client
from appwrite.query import Query

from app.core.config import Settings
from app.repositories.base import AppwriteRepository

logger = logging.getLogger(__name__)

# Conservative allow-list for profile writes before base-repo schema checks/retries.
PROFILE_ALLOWED_FIELDS = {
    "user_id",
    "name",
    "email",
    "phone",
    "location",
    "title",
    "summary",
    "profile_summary",
    "skills",
    "experience_level",
    "education",
    "strengths",
    "career_goals",
    "languages",
    "preferred_locations",
    "preferred_job_types",
    "linkedin_url",
    "github_url",
    "portfolio_url",
    "cv_data",
    "cv_hash",
    "cv_filename",
    "cv_file_id",
    "cv_text",
    "has_cv",
    "last_updated",
    "isActive",
    "is_active",
    "links",
}


class ProfileRepository(AppwriteRepository):
    """Repository for 'profiles' collection."""

    def __init__(self, client: Client, settings: Settings):
        super().__init__(
            client=client,
            database_id=settings.database_id,
            collection_id=settings.collection_id_profiles,
        )

    def _sanitize_profile_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        clean = {k: v for k, v in data.items() if k in PROFILE_ALLOWED_FIELDS}
        dropped = sorted([k for k in data.keys() if k not in clean])
        if dropped:
            logger.warning("Dropping non-profile fields: %s", ", ".join(dropped))
        return clean

    def _sanitize_against_existing_row(self, data: Dict[str, Any], row: Dict[str, Any]) -> Dict[str, Any]:
        """When schema-read scopes are missing, use existing row keys as safe update fields."""
        row_keys = {k for k in row.keys() if not k.startswith("$")}
        row_keys.add("user_id")
        clean = {k: v for k, v in data.items() if k in row_keys}
        dropped = sorted([k for k in data.keys() if k not in clean])
        if dropped:
            logger.warning("Dropping fields not present on existing profile row: %s", ", ".join(dropped))
        return clean

    def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the best profile for a user across legacy/current key names."""
        results = self.list([Query.equal("user_id", user_id), Query.order_desc("$updatedAt"), Query.limit(50)])
        if not results:
            # Backward compatibility with legacy documents.
            results = self.list([Query.equal("userId", user_id), Query.order_desc("$updatedAt"), Query.limit(50)])
        if not results:
            return None

        active = next((row for row in results if bool(row.get("isActive") or row.get("is_active"))), None)
        return active or results[0]

    def upsert_profile(self, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create or update a user profile."""
        profile = self.get_by_user_id(user_id)

        payload = dict(data)
        payload["user_id"] = user_id
        payload = self._sanitize_profile_payload(payload)

        if profile:
            payload = self._sanitize_against_existing_row(payload, profile)
            return self.update(profile["$id"], payload)

        return self.create(payload)

    def set_cv_data(self, user_id: str, cv_data: Dict[str, Any], cv_hash: str) -> bool:
        """Update profile with analyzed CV data."""
        data = {
            "cv_data": self._serialize(cv_data),
            "cv_hash": cv_hash,
            "has_cv": True,
            "last_updated": self._serialize(datetime.now().isoformat())
        }
        return self.upsert_profile(user_id, data) is not None
