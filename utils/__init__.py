"""
Utility functions for the Job Market AI Agent
"""

from .database import jobs_collection, store_jobs_in_db
from .scraping import extract_skills_from_description, semantic_skill_match, discover_new_jobs, extract_job_keywords, keyword_gap_analysis, check_api_status, API_CONFIG
from .matching import match_student_to_jobs
from .cv_tailoring import CVTailoringEngine
from .mock_interview import MockInterviewSimulator

__all__ = [
    'jobs_collection',
    'store_jobs_in_db',
    'extract_skills_from_description',
    'semantic_skill_match',
    'discover_new_jobs',
    'match_student_to_jobs',
    'extract_job_keywords',
    'keyword_gap_analysis',
    'check_api_status',
    'API_CONFIG',
    'CVTailoringEngine',
    'MockInterviewSimulator'
]
