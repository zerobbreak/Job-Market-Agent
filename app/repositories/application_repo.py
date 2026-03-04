"""
Application repository for tracking job applications.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from appwrite.client import Client
from appwrite.id import ID
from appwrite.query import Query

from app.core.config import Settings
from app.repositories.base import AppwriteRepository

logger = logging.getLogger(__name__)


class ApplicationRepository(AppwriteRepository):
    """Repository for 'applications' collection."""

    def __init__(self, client: Client, settings: Settings):
        super().__init__(
            client=client,
            database_id=settings.database_id,
            collection_id=settings.collection_id_applications,
        )

    def save_application(
        self,
        user_id: str,
        company: str,
        role: str,
        job_url: str = "",
        location: str = "",
        cv_storage_id: str = None,
        cl_storage_id: str = None,
        description: str = "",
        match_score: int = 0,
        ats_score: int = None,
    ) -> Optional[str]:
        """Ported from job_store.py:save_application."""
        now = datetime.now().isoformat()
        data = {
            "company": company,
            "role": role,
            "job_url": job_url,
            "location": location,
            "status": "generated",
            "date_created": now,
            "date_updated": now,
            "cv_storage_id": cv_storage_id,
            "cover_letter_storage_id": cl_storage_id,
            "job_description": description[:10000] if description else "",
            "match_score": match_score,
            "ats_score": ats_score,
            "user_id": user_id,
            "views": 0,
        }

        result = self.create(data)
        return result["$id"] if result else None

    def get_user_applications(
        self, user_id: str, status: str = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve applications for a specific user."""
        queries = [Query.equal("user_id", user_id), Query.order_desc("date_created"), Query.limit(limit)]
        if status:
            queries.append(Query.equal("status", status))

        return self.list(queries)

    def track_view(self, app_id: str) -> bool:
        """Increment view count."""
        doc = self.get(app_id)
        if not doc:
            return False
        
        current_views = doc.get("views", 0) or 0
        return self.update(app_id, {"views": current_views + 1}) is not None
