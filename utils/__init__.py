"""
Utility functions for the Job Market AI Agent
Simplified to only include actively used utilities.
"""


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
from .tracker import ApplicationTracker

__all__ = [

    
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
    'CVTailoringEngine',
    
    # Application Tracking
    'ApplicationTracker'
]
