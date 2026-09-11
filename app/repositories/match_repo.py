"""
Match repository for managing matched job search results.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import delete as sa_delete
from sqlalchemy import update as sa_update

from app.core.config import Settings
from app.core.database import Match, get_session
from app.repositories.postgres_base import TypedRepository
from app.repositories.query import Query

logger = logging.getLogger(__name__)


class MatchRepository(TypedRepository):
    """Repository for job matches — one row per (user, matched job) pair."""

    model = Match

    def __init__(self, settings: Settings):
        super().__init__()

    def get_user_matches(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve a user's cached matches, best score first."""
        rows = self.list([Query.equal("user_id", user_id), Query.order_desc("match_score")])
        if not rows:
            return None
        return [self._to_match_view(r) for r in rows]

    @staticmethod
    def _to_match_view(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "job": {
                "id": row.get("job_hash"),
                "title": row.get("title"),
                "company": row.get("company"),
                "location": row.get("location"),
                "description": row.get("description"),
                "url": row.get("url"),
            },
            "match_score": row.get("match_score"),
            "match_reasons": row.get("match_reasons") or [],
            "score_breakdown": row.get("score_breakdown") or {},
            "semantic_score": row.get("semantic_score"),
        }

    def cache_matches(self, user_id: str, location: str, matches: List[Dict[str, Any]]) -> bool:
        """Replace a user's cached matches with a freshly scored batch."""
        try:
            now = datetime.now(timezone.utc)
            seen_job_hashes: set[str] = set()

            with get_session() as session:
                session.execute(sa_delete(Match).where(Match.user_id == user_id))

                for match in matches:
                    job = match.get("job", {}) or {}
                    job_hash = str(job.get("id") or job.get("url") or uuid.uuid4().hex)[:500]
                    if job_hash in seen_job_hashes:
                        continue
                    seen_job_hashes.add(job_hash)

                    session.add(Match(
                        id=uuid.uuid4().hex,
                        user_id=user_id,
                        job_hash=job_hash,
                        title=job.get("title", ""),
                        company=job.get("company", ""),
                        location=job.get("location") or location,
                        url=job.get("url", ""),
                        description=job.get("description", ""),
                        match_score=match.get("match_score"),
                        semantic_score=match.get("semantic_score"),
                        keyword_score=(match.get("score_breakdown") or {}).get("keyword"),
                        score_breakdown=match.get("score_breakdown") or {},
                        match_reasons=match.get("match_reasons") or [],
                        attrs={},
                        created_at=now,
                        updated_at=now,
                    ))
                session.commit()
            return True
        except Exception as e:
            logger.error("Error caching matches for user %s: %s", user_id, e)
            return False

    def update_last_seen(self, user_id: str) -> bool:
        """Mark all of a user's cached matches as seen."""
        try:
            with get_session() as session:
                session.execute(
                    sa_update(Match)
                    .where(Match.user_id == user_id)
                    .values(last_seen=datetime.now(timezone.utc))
                )
                session.commit()
            return True
        except Exception as e:
            logger.error("Error updating last_seen for user %s: %s", user_id, e)
            return False
