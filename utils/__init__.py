"""
Utility functions for the Job Market AI Agent
"""

from .database import jobs_collection, store_jobs_in_db
from .scraping import extract_skills_from_description, semantic_skill_match, discover_new_jobs, extract_job_keywords, keyword_gap_analysis, check_api_status, API_CONFIG
from .matching import match_student_to_jobs
from .cv_tailoring import CVTailoringEngine
from .mock_interview import MockInterviewSimulator
from .knowledge_base import knowledge_base, KnowledgeBase
from .sa_customizations import sa_customizations, SACustomizations
from .ethical_guidelines import ethical_guidelines, EthicalGuidelines
from .config import settings, get_settings
from .exceptions import JobMarketAnalyzerError, CVProcessingError, JobScrapingError, APIError, DatabaseError, ConfigurationError, ValidationError, AuthenticationError
from .scrapper import scrape_all, scrape_all_advanced, AdvancedJobScraper, advanced_scraper

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
    'MockInterviewSimulator',
    'knowledge_base',
    'KnowledgeBase',
    'sa_customizations',
    'SACustomizations',
    'ethical_guidelines',
    'EthicalGuidelines',
    'settings',
    'get_settings',
    'JobMarketAnalyzerError',
    'CVProcessingError',
    'JobScrapingError',
    'APIError',
    'DatabaseError',
    'ConfigurationError',
    'ValidationError',
    'AuthenticationError',
    'scrape_all',
    'scrape_all_advanced',
    'AdvancedJobScraper',
    'advanced_scraper'
]
