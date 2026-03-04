"""
Job repository for managing job state and matching results.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from appwrite.client import Client

from app.core.config import Settings
from app.repositories.base import AppwriteRepository

logger = logging.getLogger(__name__)


class JobRepository(AppwriteRepository):
    """Repository for 'jobs' collection."""

    def __init__(self, client: Client, settings: Settings):
        super().__init__(
            client=client,
            database_id=settings.database_id,
            collection_id=settings.collection_id_jobs,
        )

    def save_state(self, job_id: str, state: Dict[str, Any]) -> bool:
        """Ported from job_store.py:save_job_state."""
        data = {
            "title": str(state.get("title", "Preview Job"))[:255],
            "company": str(state.get("company", "Unknown"))[:255],
            "status": state.get("status", "initializing"),
            "progress": int(state.get("progress", 0)),
            "phase": state.get("phase", ""),
            "job_data": self._serialize(state.get("job_data")),
            "result": self._serialize(state.get("result")),
            "template_type": state.get("template_type", "modern"),
            "user_id": state.get("user_id", ""),
            "error": state.get("error", ""),
        }

        if self.get(job_id):
            return self.update(job_id, data) is not None
        return self.create(data, document_id=job_id) is not None

    def load_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Ported from job_store.py:load_job_state."""
        doc = self.get(job_id)
        if not doc:
            return None

        return {
            "id": doc.get("$id"),
            "status": doc.get("status"),
            "progress": doc.get("progress"),
            "phase": doc.get("phase"),
            "job_data": self._deserialize(doc.get("job_data")),
            "result": self._deserialize(doc.get("result")),
            "template_type": doc.get("template_type"),
            "user_id": doc.get("user_id"),
            "error": doc.get("error"),
            "updated_at": doc.get("$updatedAt"),
        }

    def update_progress(
        self,
        job_id: str,
        progress: int,
        status: str = None,
        phase: str = None,
        error: str = None,
        result: dict = None,
    ) -> bool:
        """Ported from job_store.py:update_job_progress."""
        data: Dict[str, Any] = {"progress": int(progress)}
        if status:
            data["status"] = status
        if phase:
            data["phase"] = phase
        if error:
            data["error"] = error
            data["status"] = "error"
        if result:
            data["result"] = self._serialize(result)
            data["status"] = "done"
            data["progress"] = 100

        return self.update(job_id, data) is not None
