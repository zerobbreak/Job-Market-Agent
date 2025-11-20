"""
Watcher Service
Background service that monitors job boards and notifies users of new opportunities.
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.scraping import AdvancedJobScraper, ScraperConfig
from utils.memory_store import memory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JobWatcher:
    """
    Background service that watches for new job opportunities.
    """
    
    def __init__(self, check_interval_hours: int = 6, config: ScraperConfig = None):
        """
        Initialize the watcher.
        
        Args:
            check_interval_hours: How often to check for new jobs (in hours)
            config: Optional ScraperConfig for customizing scraper behavior
        """
        self.check_interval = check_interval_hours * 3600  # Convert to seconds
        
        # Use custom config or create one optimized for watching
        if config is None:
            config = ScraperConfig(
                cache_max_age_hours=check_interval_hours,  # Match check interval
                default_results_wanted=15,  # Reasonable for watching
                enable_ai_descriptions=False,  # Save API costs for background watching
                log_file='watcher.log'  # Separate log file
            )
        
        self.scraper = AdvancedJobScraper(config=config)
        self.notification_log = []
        logger.info(f" JobWatcher initialized (checking every {check_interval_hours}h)")
        
    def check_for_new_jobs(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check for new jobs based on search parameters.
        
        Args:
            search_params: Dictionary with 'query', 'location', etc.
            
        Returns:
            List of new high-match jobs
        """
        logger.info(f" Checking for new jobs: {search_params}")
        
        try:
            # Use the new scrape_with_advanced_features method
            jobs = self.scraper.scrape_with_advanced_features(
                search_term=search_params.get('query', 'Python Developer'),
                location=search_params.get('location', 'South Africa'),
                results_wanted=search_params.get('results_wanted', 15),
                use_cache=True,  # Use cache to avoid redundant scraping
                enable_url_scraping=False,  # Disable for speed in background
                enable_ai_descriptions=False,  # Disable to save API costs
            )
            
            if not jobs:
                logger.info("  No jobs found")
                return []
            
            # Filter for high-match jobs and check for new ones
            new_jobs = []
            for job in jobs:
                # Check if we've seen this job before
                job_signature = f"{job.get('title')} at {job.get('company')}"
                similar = memory.find_similar_jobs(job_signature)
                
                # If no similar jobs in memory, it's new
                if not similar:
                    new_jobs.append(job)
                    # Save to memory
                    memory.save_job(job)
                    logger.debug(f"✨ New job found: {job_signature}")
                    
            logger.info(f" Found {len(new_jobs)} new jobs out of {len(jobs)} total")
            return new_jobs
            
        except Exception as e:
            logger.error(f" Error checking for jobs: {e}", exc_info=True)
            return []
    
    def notify_user(self, jobs: List[Dict[str, Any]]):
        """
        Notify the user of new jobs.
        For now, just log them. In production, this could send emails, push notifications, etc.
        
        Args:
            jobs: List of new jobs to notify about
        """
        if not jobs:
            logger.info(" No new jobs to notify about")
            return
            
        logger.info(f"\n{'='*60}")
        logger.info(f" NEW JOB ALERT - {len(jobs)} opportunities found!")
        logger.info(f"{'='*60}")
        
        for i, job in enumerate(jobs, 1):
            logger.info(f"\n{i}. {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
            logger.info(f"    Location: {job.get('location', 'N/A')}")
            logger.info(f"    URL: {job.get('url', 'N/A')}")
            logger.info(f"    Relevance: {job.get('relevance_score', 0):.2f}")
            
            # Show skills if available
            skills = job.get('skills', [])
            if skills:
                logger.info(f"   🛠️  Skills: {', '.join(skills[:5])}")
            
            # Show salary if available
            salary_info = job.get('salary_info', {})
            if salary_info and salary_info.get('salary_min'):
                currency = salary_info.get('salary_currency', 'USD')
                min_sal = salary_info.get('salary_min')
                max_sal = salary_info.get('salary_max')
                logger.info(f"    Salary: {currency} {min_sal:,} - {max_sal:,}")
            
        logger.info(f"\n{'='*60}\n")
            
        self.notification_log.append({
            "timestamp": datetime.now().isoformat(),
            "count": len(jobs),
            "jobs": jobs
        })
        
        logger.info(f" Notification logged ({len(self.notification_log)} total notifications)")
    
    def run_once(self, search_params: Dict[str, Any]):
        """
        Run a single check cycle.
        
        Args:
            search_params: Search parameters for job scraping
        """
        logger.info("🚀 Starting job watch cycle...")
        start_time = time.time()
        
        new_jobs = self.check_for_new_jobs(search_params)
        self.notify_user(new_jobs)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Watch cycle complete in {elapsed:.2f}s")
    
    def run_continuous(self, search_params: Dict[str, Any]):
        """
        Run the watcher continuously in the background.
        
        Args:
            search_params: Search parameters for job scraping
        """
        logger.info(f" Starting continuous job watcher (checking every {self.check_interval/3600:.1f} hours)")
        logger.info(f" Search params: {search_params}")
        
        cycle_count = 0
        while True:
            try:
                cycle_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f" Watch Cycle #{cycle_count}")
                logger.info(f"{'='*60}")
                
                self.run_once(search_params)
                
                # Periodic cache cleanup (every 24 hours worth of cycles)
                cycles_per_day = 24 / (self.check_interval / 3600)
                if cycle_count % max(1, int(cycles_per_day)) == 0:
                    logger.info(" Running periodic cache cleanup...")
                    self.scraper.cleanup_cache()
                
                logger.info(f" Sleeping for {self.check_interval/3600:.1f} hours...")
                logger.info(f"   Next check at: {datetime.fromtimestamp(time.time() + self.check_interval).strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("\n Watcher stopped by user")
                logger.info(f" Total cycles completed: {cycle_count}")
                logger.info(f" Total notifications sent: {len(self.notification_log)}")
                break
            except Exception as e:
                logger.error(f"❌ Error in watch cycle: {e}", exc_info=True)
                logger.info("⏳ Waiting 1 minute before retrying...")
                time.sleep(60)  # Wait 1 minute before retrying

def main():
    """
    Main entry point for the watcher service.
    """
    logger.info("="*60)
    logger.info(" JOB WATCHER SERVICE")
    logger.info("="*60)
    
    # Example search parameters - customize these
    search_params = {
        "query": "Python Developer",
        "location": "South Africa",
        "results_wanted": 15
    }
    
    # Create custom config for watcher (optional)
    watcher_config = ScraperConfig(
        cache_max_age_hours=6,  # Match check interval
        default_results_wanted=15,
        enable_ai_descriptions=False,  # Save API costs
        log_file='watcher.log'
    )
    
    watcher = JobWatcher(check_interval_hours=6, config=watcher_config)
    
    # Run once for testing
    logger.info(" Running single test cycle...")
    watcher.run_once(search_params)
    
    # Uncomment to run continuously
    logger.info("\n Starting continuous monitoring...")
    watcher.run_continuous(search_params)

if __name__ == "__main__":
    main()
