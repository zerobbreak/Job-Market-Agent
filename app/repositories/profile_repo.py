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


class ProfileRepository(AppwriteRepository):
    """Repository for 'profiles' collection."""

    def __init__(self, client: Client, settings: Settings):
        super().__init__(
            client=client,
            database_id=settings.database_id,
            collection_id=settings.collection_id_profiles,
        )

    def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve profile by user ID."""
        results = self.list([Query.equal("user_id", user_id), Query.limit(1)])
        return results[0] if results else None

    def upsert_profile(self, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create or update a user profile."""
        profile = self.get_by_user_id(user_id)
        
        # Ensure user_id is in the data
        data["user_id"] = user_id
        
        if profile:
            return self.update(profile["$id"], data)
        return self.create(data)

    def set_cv_data(self, user_id: str, cv_data: Dict[str, Any], cv_hash: str) -> bool:
        """Update profile with analyzed CV data."""
        data = {
            "cv_data": self._serialize(cv_data),
            "cv_hash": cv_hash,
            "has_cv": True,
            "last_updated": self._serialize(datetime.now().isoformat())
        }
        return self.upsert_profile(user_id, data) is not None
