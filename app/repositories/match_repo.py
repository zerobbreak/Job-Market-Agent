"""
Match repository for managing matched job search results.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import Settings
from app.repositories.postgres_base import PostgresRepository
from app.repositories.query import Query

logger = logging.getLogger(__name__)


class MatchRepository(PostgresRepository):
    """Repository for 'matches' collection."""

    def __init__(self, settings: Settings):
        super().__init__(collection=settings.collection_id_matches)

    def get_user_matches(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the most recent matches for a user."""
        queries = [Query.equal("user_id", user_id), Query.order_desc("$createdAt"), Query.limit(1)]
        results = self.list(queries)
        return results[0] if results else None

    def cache_matches(self, user_id: str, location: str, matches: List[Dict[str, Any]]) -> bool:
        """Cache fresh matching results."""
        match_doc_id = f"match_{user_id}"
        data = {
            "user_id": user_id,
            "userId": user_id,
            "location": location,
            "matches": self._serialize(matches),
            "last_seen": datetime.now().isoformat(),
        }

        if self.get(match_doc_id):
            return self.update(match_doc_id, data) is not None
        return self.create(data, document_id=match_doc_id) is not None

    def update_last_seen(self, document_id: str) -> bool:
        """Update last_seen timestamp."""
        return self.update(document_id, {"last_seen": datetime.now().isoformat()}) is not None
