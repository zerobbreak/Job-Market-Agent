"""
Application service for managing job applications.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import Settings
from app.repositories.application_repo import ApplicationRepository

logger = logging.getLogger(__name__)


class ApplicationService:
    """Service for job application-related business logic."""

    def __init__(
        self,
        settings: Settings,
        application_repo: ApplicationRepository,
    ):
        self.settings = settings
        self.app_repo = application_repo

    async def list_applications(
        self, user_id: str, page: int = 1, limit: int = 10
    ) -> Dict[str, Any]:
        """List job applications for a user with pagination."""
        offset = (page - 1) * limit
        results, total = self.app_repo.list_for_user(user_id, limit=limit, offset=offset)

        applications = []
        for doc in results:
            applications.append({
                "id": doc["$id"],
                "jobTitle": doc.get("jobTitle", "Unknown Position"),
                "company": doc.get("company", "Unknown Company"),
                "jobUrl": doc.get("jobUrl", ""),
                "location": doc.get("location", ""),
                "status": doc.get("status", "applied"),
                "appliedDate": doc.get("$createdAt", "").split("T")[0],
                "files": doc.get("files"),
            })

        return {
            "applications": applications,
            "page": page,
            "limit": limit,
            "total": total,
        }

    async def update_status(
        self, user_id: str, application_id: str, new_status: str
    ) -> Tuple[bool, Optional[str]]:
        """Update application status with ownership verification."""
        allowed = {"pending", "applied", "interview", "rejected"}
        if new_status not in allowed:
            return False, "Invalid status"

        doc = self.app_repo.get(application_id)
        if not doc:
            return False, "Application not found"

        if doc.get("userId") != user_id:
            return False, "Forbidden"

        success = self.app_repo.update(application_id, {"status": new_status})
        if not success:
            return False, "Database update failed"

        return True, None
