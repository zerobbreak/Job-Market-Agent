"""
Job service for orchestrating job search, matching, and scoring.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import Settings
from app.repositories.job_repo import JobRepository
from app.repositories.profile_repo import ProfileRepository
from app.schemas.job import JobResponse, JobSearchRequest

logger = logging.getLogger(__name__)


class JobService:
    """Service for job-related business logic."""

    def __init__(
        self,
        settings: Settings,
        job_repo: JobRepository,
        profile_repo: ProfileRepository,
    ):
        self.settings = settings
        self.job_repo = job_repo
        self.profile_repo = profile_repo

    async def search_and_match(
        self, user_id: str, request: JobSearchRequest
    ) -> Dict[str, Any]:
        """Perform fresh job search and semantic matching."""
        # 1. Get user profile
        profile = self.profile_repo.get_by_user_id(user_id)
        if not profile:
            return {"success": False, "error": "Profile not found. Please upload a CV first."}

        profile_data = {
            "name": profile.get("name", ""),
            "email": profile.get("email", ""),
            "skills": self.profile_repo._deserialize(profile.get("skills", "[]")),
            "experience_level": profile.get("experience_level", ""),
            "education": profile.get("education", ""),
            "career_goals": profile.get("career_goals", ""),
            "location": profile.get("location", request.location or "South Africa"),
            "strengths": self.profile_repo._deserialize(profile.get("strengths", "[]")),
        }

        # 2. Orchestrate search via existing pipeline (to be refactored later)
        from services.pipeline_service import JobApplicationPipeline
        from services.matching_service import SemanticMatcher

        pipeline = JobApplicationPipeline()
        location_str = (request.location or profile_data.get("location") or "South Africa").strip()

        # 3. Generate query logic
        search_query = request.query.strip() if request.query else ""
        
        if not search_query:
            skills = profile_data.get("skills", [])
            top_skill = (skills + ["Developer"])[0]
            exp_level = profile_data.get("experience_level", "")
            role_title = profile_data.get("career_goals", f"{top_skill} Developer")
            
            search_query = f"{exp_level} {role_title}".strip()
            if len(search_query) > 60:
                 search_query = f"{exp_level} {top_skill} Developer".strip()

        logger.info("Starting fresh matching for user %s with query: %s", user_id, search_query)

        jobs = pipeline.search_jobs(
            query=search_query,
            location=location_str,
            max_results=request.max_results * 2,
            use_cache=False,
        )

        if not jobs:
            return {"success": True, "matches": [], "total_matches": 0, "message": "No jobs found"}

        # 3. Semantic scoring
        matcher = SemanticMatcher()
        matched_jobs = []
        for job in jobs:
            if job.get("is_closed"):
                continue
            
            match_result = matcher.calculate_match(profile_data, job)
            if match_result.total_score >= 0.0:  # In production we might use a threshold
                job["match_score"] = match_result.total_score
                job["match_reasons"] = match_result.explanation
                job["semantic_score"] = match_result.semantic_score
                job["score_breakdown"] = {
                    "semantic": match_result.semantic_score,
                    "keyword": match_result.keyword_score,
                }
                matched_jobs.append(job)

        # 4. Sort and format
        matched_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        matched_jobs = matched_jobs[:request.max_results]

        formatted_matches = []
        for job in matched_jobs:
            formatted_matches.append({
                "job": {
                    "id": str(job.get("job_hash", job.get("url", ""))),
                    "title": job.get("title", "Unknown"),
                    "company": job.get("company", "Unknown"),
                    "location": job.get("location", ""),
                    "description": job.get("description", "")[:500],
                    "url": job.get("url", ""),
                },
                "match_score": round(float(job.get("match_score", 0)), 1),
                "match_reasons": job.get("match_reasons", []),
                "score_breakdown": job.get("score_breakdown", {}),
                "semantic_score": round(float(job.get("semantic_score", 0)), 1),
            })

        # 5. Persistent cache (to be moved to a dedicated match_repo if needed)
        # Ported logic for match caching...
        # For now, we'll use the job_repo to store this or create a MatchRepository.
        
        return {
            "success": True,
            "matches": formatted_matches,
            "location": location_str,
            "cached": False,
            "total_matches": len(formatted_matches),
        }

    async def get_cached_matches(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve last cached matches for user."""
        # This currently uses a 'matches' collection in Appwrite.
        # I should create a MatchRepository.
        pass
