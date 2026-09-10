"""
Scraper configuration.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScraperConfig:
    """Centralized scraper configuration"""
    cache_dir: str = "job_cache"
    cache_max_age_hours: int = 24
    cache_max_size_mb: int = 100
    default_results_wanted: int = 20
    default_hours_old: int = 72
    default_platforms: list = field(default_factory=lambda: ["indeed", "linkedin", "zip_recruiter", "glassdoor"])
    
    # Platform-specific settings
    indeed_limit: int = 50
    linkedin_limit: int = 25
    
    # AI Enrichment settings
    ai_model_name: str = "gemini-1.5-flash"
    ai_temperature: float = 0.7
    ai_max_tokens: int = 2000
    
    # Execution settings
    enable_parallel_processing: bool = True
    max_workers: int = 5
    
    # Logging
    log_level: int = logging.INFO
    log_file: str = "scraper.log"

    @classmethod
    def from_env(cls) -> "ScraperConfig":
        """Load config from environment variables"""
        return cls(
            cache_dir=os.getenv("SCRAPER_CACHE_DIR", "job_cache"),
            cache_max_age_hours=int(os.getenv("SCRAPER_CACHE_AGE", "24")),
            ai_model_name=os.getenv("SCRAPER_MODEL", "gemini-1.5-flash"),
            enable_parallel_processing=os.getenv("SCRAPER_PARALLEL", "true").lower() == "true",
        )
