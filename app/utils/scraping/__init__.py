"""
Scraping utility subpackage.
"""

from .core import AdvancedJobScraper
from .config import ScraperConfig
from .enrichment import (
    extract_skills_from_description,
    extract_job_keywords,
    keyword_gap_analysis,
    semantic_skill_match
)

__all__ = [
    "AdvancedJobScraper", 
    "ScraperConfig",
    "extract_skills_from_description",
    "extract_job_keywords",
    "keyword_gap_analysis",
    "semantic_skill_match"
]
