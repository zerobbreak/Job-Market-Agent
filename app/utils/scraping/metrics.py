"""
Scraper performance metrics tracking.
"""

import logging
from dataclasses import dataclass


@dataclass
class ScraperMetrics:
    """Track scraper performance metrics"""
    total_jobs_scraped: int = 0
    total_jobs_deduplicated: int = 0
    total_jobs_enriched: int = 0
    total_api_calls: int = 0
    total_cache_hits: int = 0
    total_cache_misses: int = 0
    total_errors: int = 0
    scraping_time_seconds: float = 0.0
    enrichment_time_seconds: float = 0.0

    def to_dict(self):
        return vars(self)

    def log_summary(self, logger: logging.Logger):
        """Log metrics summary"""
        logger.info("Scraping Summary:")
        logger.info(f"  Jobs Scraped: {self.total_jobs_scraped}")
        logger.info(f"  Deduplicated: {self.total_jobs_deduplicated}")
        logger.info(f"  Enriched: {self.total_jobs_enriched}")
        logger.info(f"  Cache Hits: {self.total_cache_hits}")
        logger.info(f"  API Calls: {self.total_api_calls}")
        logger.info(f"  Scraping Time: {self.scraping_time_seconds:.2f}s")
        logger.info(f"  Enrichment Time: {self.enrichment_time_seconds:.2f}s")

    @property
    def cache_hit_rate(self) -> float:
        total = self.total_cache_hits + self.total_cache_misses
        return self.total_cache_hits / total if total > 0 else 0.0

    @property
    def error_rate(self) -> float:
        total = self.total_api_calls
        return self.total_errors / total if total > 0 else 0.0

    @property
    def total_time(self) -> float:
        return self.scraping_time_seconds + self.enrichment_time_seconds
