"""
Core job scraping logic using jobspy.
"""

import os
import re
import time
import json
import hashlib
import logging
import random
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import jobspy
try:
    from jobspy import scrape_jobs
    JOBSPY_AVAILABLE = True
except ImportError:
    JOBSPY_AVAILABLE = False
    logging.warning("jobspy not available. Job scraping features will be limited.")

from .config import ScraperConfig
from .metrics import ScraperMetrics
from .helpers import RateLimiter, retry_with_backoff

logger = logging.getLogger(__name__)


class AdvancedJobScraper:
    """
    Advanced job scraper with deduplication, scoring, caching, and enrichment features.
    Delegates AI enrichment to specialized modules.
    """

    def __init__(self, config: Optional[ScraperConfig] = None):
        """Initialize scraper with configuration and metrics"""
        self.config = config or ScraperConfig()
        self.cache_dir = self.config.cache_dir
        self.metrics = ScraperMetrics()
        # Default rate limit if not in config
        max_rpm = getattr(self.config, 'max_requests_per_minute', 30)
        self.rate_limiter = RateLimiter(
            max_calls=max_rpm,
            time_window=60.0
        )
        self.setup_logging(self.config.log_level)
        self.setup_cache()

    def setup_logging(self, log_level: int):
        """Setup logger for the scraper."""
        self.logger = logger
        self.logger.setLevel(log_level)

    def setup_cache(self):
        """Setup caching directory"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            self.logger.info(f"Created cache directory: {self.cache_dir}")

    def _get_random_header(self) -> Dict[str, str]:
        """Generate random User-Agent headers to avoid detection"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        ]
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive',
        }

    def _base_params(self, search_term: str, location: str, **overrides) -> Dict[str, Any]:
        """Build base params shared across all platforms"""
        params = {
            'search_term': search_term,
            'location': location,
            'results_wanted': overrides.get('results_wanted', self.config.default_results_wanted),
            'hours_old': overrides.get('hours_old', self.config.default_hours_old),
            'description_format': overrides.get('description_format', 'markdown'),
            'verbose': overrides.get('verbose', 0),
        }
        # Optional filters
        for key in ['job_type', 'is_remote', 'distance']:
            val = overrides.get(key)
            if val is not None:
                params[key] = val
        return params

    @retry_with_backoff()
    def scrape_platform(self, platform: str, search_term: str, location: str, **overrides) -> List[Dict[str, Any]]:
        """Scrape jobs from a specific platform."""
        if not JOBSPY_AVAILABLE:
            self.logger.error("jobspy is not installed.")
            return []

        params = self._base_params(search_term, location, **overrides)
        params['site_name'] = [platform]
        
        # Site-specific overrides
        if platform == 'indeed':
            params['country_indeed'] = overrides.get('country', 'south africa')
        elif platform == 'linkedin':
            params['linkedin_fetch_description'] = True

        self.logger.info(f"Scraping {platform} for '{search_term}' in '{location}'")
        
        try:
            jobs_df = scrape_jobs(**params)
            if jobs_df is None or jobs_df.empty:
                return []
            return self._normalize_results(jobs_df)
        except Exception as e:
            self.logger.error(f"Error scraping {platform}: {e}")
            return []

    def _normalize_results(self, jobs_df) -> List[Dict[str, Any]]:
        """Normalize jobspy results to a common format."""
        raw_jobs = []
        for _, row in jobs_df.iterrows():
            job_dict = {
                'title': str(row.get('title', 'N/A')),
                'company': str(row.get('company', 'N/A')),
                'location': str(row.get('location', 'N/A')),
                'url': str(row.get('job_url', 'N/A')),
                'description': str(row.get('description', '')),
                'source': str(row.get('site', 'unknown')),
                'date_posted': str(row.get('date_posted', 'N/A')),
                'job_type': str(row.get('job_type', 'N/A')),
                'is_remote': row.get('is_remote'),
                'salary_min': row.get('min_amount'),
                'salary_max': row.get('max_amount'),
                'currency': row.get('currency', 'USD'),
            }
            raw_jobs.append(job_dict)
        return raw_jobs

    def deduplicate_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate jobs."""
        seen = set()
        unique = []
        for job in jobs:
            key = f"{job['title']}|{job['company']}|{job['location']}"
            h = hashlib.md5(key.encode()).hexdigest()
            if h not in seen:
                seen.add(h)
                unique.append(job)
        self.metrics.total_jobs_deduplicated = len(unique)
        return unique

    def get_cache_key(self, search_term: str, location: str, platforms: List[str]) -> str:
        """Generate a cache key for search parameters."""
        key_str = f"{search_term}_{location}_{sorted(platforms)}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def load_from_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Load results from cache if valid."""
        filepath = os.path.join(self.cache_dir, f"{cache_key}.json")
        if not os.path.exists(filepath):
            return None
        
        stat = os.stat(filepath)
        age_hours = (time.time() - stat.st_mtime) / 3600
        if age_hours > self.config.cache_max_age_hours:
            return None

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                self.metrics.total_cache_hits += 1
                return data
        except Exception:
            return None

    def save_to_cache(self, cache_key: str, jobs: List[Dict[str, Any]]):
        """Save results to cache."""
        filepath = os.path.join(self.cache_dir, f"{cache_key}.json")
        try:
            with open(filepath, 'w') as f:
                json.dump(jobs, f)
        except Exception as e:
            self.logger.error(f"Error saving to cache: {e}")

    async def run_search(self, search_term: str, location: str, platforms: Optional[List[str]] = None, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Run a full search across multiple platforms."""
        start_time = time.time()
        platforms = platforms or self.config.default_platforms
        
        if use_cache:
            cache_key = self.get_cache_key(search_term, location, platforms)
            cached = self.load_from_cache(cache_key)
            if cached:
                self.logger.info(f"Using cached results for {search_term}")
                return cached

        all_jobs = []
        if self.config.enable_parallel_processing:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = [executor.submit(self.scrape_platform, p, search_term, location) for p in platforms]
                for future in as_completed(futures):
                    all_jobs.extend(future.result())
        else:
            for p in platforms:
                all_jobs.extend(self.scrape_platform(p, search_term, location))

        unique_jobs = self.deduplicate_jobs(all_jobs)
        self.metrics.total_jobs_scraped = len(unique_jobs)
        self.metrics.scraping_time_seconds = time.time() - start_time
        
        if use_cache:
            self.save_to_cache(cache_key, unique_jobs)
            
        return unique_jobs
