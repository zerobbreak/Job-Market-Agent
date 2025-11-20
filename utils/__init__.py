"""
Utility functions for the Job Market AI Agent
Simplified to only include actively used utilities.
"""

from .memory_store import memory, MemoryStore
from .scraping import (
    AdvancedJobScraper,
    extract_skills_from_description,
    semantic_skill_match,
    discover_new_jobs,
    extract_job_keywords,
    keyword_gap_analysis,
    check_api_status,
    API_CONFIG
)
from .cv_tailoring import CVTailoringEngine

__all__ = [
    # Memory Store
    'memory',
    'MemoryStore',
    
    # Job Scraping
    'AdvancedJobScraper',
    'extract_skills_from_description',
    'semantic_skill_match',
    'discover_new_jobs',
    'extract_job_keywords',
    'keyword_gap_analysis',
    'check_api_status',
    'API_CONFIG',
    
    # CV Tailoring
    'CVTailoringEngine'
]
