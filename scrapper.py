import json
import os
import hashlib
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from jobspy import scrape_jobs
import pandas as pd
import logging

def scrape_all(job_title, location, **kwargs):
    """
    Scrape jobs using jobspy package with full parameter support

    Args:
        job_title (str): Job search term (maps to search_term)
        location (str): Location for job search
        **kwargs: Full jobspy scrape_jobs parameters:
            - site_name (list|str): Sites to scrape ["indeed", "linkedin", "google", "glassdoor", "zip_recruiter", "bayt", "bdjobs"] (default: all)
            - search_term (str): Job search term (auto-set from job_title)
            - google_search_term (str): Custom Google search term
            - location (str): Location (auto-set)
            - distance (int): Search radius in miles (default: 50)
            - job_type (str): "fulltime", "parttime", "internship", "contract"
            - proxies (list): Proxy list ['user:pass@host:port']
            - is_remote (bool): Filter for remote jobs
            - results_wanted (int): Number of results per site (default: 20)
            - easy_apply (bool): Filter for easy apply jobs
            - user_agent (str): Custom user agent
            - description_format (str): "markdown" or "html" (default: "markdown")
            - offset (int): Start search from offset
            - hours_old (int): Filter by hours since posted (default: 72)
            - verbose (int): Logging level 0-2 (default: 2)
            - linkedin_fetch_description (bool): Get full LinkedIn descriptions
            - linkedin_company_ids (list[int]): Specific LinkedIn company IDs
            - country_indeed (str): Country filter for Indeed/Glassdoor (default: 'USA')
            - enforce_annual_salary (bool): Convert wages to annual salary
            - ca_cert (str): Path to CA certificate for proxies
    """
    print(f"\n🔍 Scraping jobs for: {job_title} in {location}")
    print("=" * 60)

    # Set default parameters
    default_params = {
        'site_name': ["indeed", "linkedin", "google"],  # Default sites
        'search_term': job_title,
        'location': location,
        'results_wanted': 20,
        'hours_old': 72,
        'country_indeed': 'USA',
        'verbose': 2  # Show all logs by default
    }

    # Update with any provided kwargs
    params = {**default_params, **kwargs}

    # Add google_search_term if not provided
    if 'google_search_term' not in params:
        params['google_search_term'] = f"{job_title} jobs near {location} since yesterday"

    try:
        # Scrape jobs using jobspy
        jobs_df = scrape_jobs(**params)

        print(f"✅ Found {len(jobs_df)} jobs")

        # Convert DataFrame to list of dictionaries for compatibility
        jobs_list = []
        for _, row in jobs_df.iterrows():
            job_dict = {
                'title': row.get('title', 'N/A'),
                'company': row.get('company', 'N/A'),
                'location': row.get('location', 'N/A'),
                'url': row.get('job_url', 'N/A'),
                'description': row.get('description', ''),
                'source': row.get('site', 'N/A'),
                'date_posted': str(row.get('date_posted', 'N/A'))
            }
            jobs_list.append(job_dict)

        # Save results
        if jobs_list:
            with open("jobs.json", "w", encoding="utf-8") as f:
                json.dump(jobs_list, f, ensure_ascii=False, indent=2)
            print("💾 Saved results to jobs.json")
        else:
            print("⚠️ No jobs found to save")

        return jobs_list

    except Exception as e:
        print(f"❌ Error scraping jobs: {e}")
        return []


class AdvancedJobScraper:
    """
    Advanced job scraper with deduplication, scoring, caching, and enrichment features
    """

    def __init__(self, cache_dir: str = "job_cache", log_level: int = logging.INFO):
        self.cache_dir = cache_dir
        self.setup_logging(log_level)
        self.setup_cache()

    def setup_logging(self, log_level: int):
        """Setup advanced logging"""
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_cache(self):
        """Setup caching directory"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            self.logger.info(f"Created cache directory: {self.cache_dir}")

    def generate_job_hash(self, job: Dict[str, Any]) -> str:
        """Generate unique hash for job deduplication"""
        key = f"{job.get('title', '')}|{job.get('company', '')}|{job.get('location', '')}"
        return hashlib.md5(key.encode()).hexdigest()

    def deduplicate_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate jobs based on title, company, and location"""
        seen = set()
        unique_jobs = []

        for job in jobs:
            job_hash = self.generate_job_hash(job)
            if job_hash not in seen:
                seen.add(job_hash)
                unique_jobs.append(job)
            else:
                self.logger.debug(f"Duplicate job removed: {job.get('title', 'Unknown')}")

        self.logger.info(f"Deduplicated {len(jobs)} -> {len(unique_jobs)} jobs")
        return unique_jobs

    def clean_job_data(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and validate job data"""
        cleaned_jobs = []

        for job in jobs:
            try:
                # Handle NaN descriptions
                if pd.isna(job.get('description')) or job.get('description') == 'NaN':
                    job['description'] = f"Job description not available. {job.get('title', '')} position at {job.get('company', 'Company')}."

                # Clean and standardize location
                location = job.get('location', '').strip()
                if location and location != 'N/A':
                    # Remove extra whitespace and standardize format
                    location = re.sub(r'\s+', ' ', location)
                    job['location'] = location

                # Validate URL
                url = job.get('url', '').strip()
                if url and not url.startswith(('http://', 'https://')):
                    job['url'] = f"https://{url}"

                # Ensure required fields exist
                job.setdefault('title', 'Unknown Title')
                job.setdefault('company', 'Unknown Company')
                job.setdefault('location', 'Unknown Location')
                job.setdefault('url', 'N/A')
                job.setdefault('source', 'unknown')

                cleaned_jobs.append(job)

            except Exception as e:
                self.logger.warning(f"Error cleaning job data: {e}")
                continue
        
        self.logger.info(f"Cleaned {len(cleaned_jobs)} jobs")
        return cleaned_jobs

    def extract_salary_info(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Extract salary information from job description and title"""
        salary_info = {
            'salary_min': None,
            'salary_max': None,
            'salary_currency': 'USD',
            'salary_period': 'yearly'
        }

        text = f"{job.get('title', '')} {job.get('description', '')}".lower()

        # Common salary patterns
        patterns = [
            r'\$([0-9,]+)\s*(?:-|to|–)\s*\$([0-9,]+)',  # $50,000 - $70,000
            r'\$([0-9,]+)',  # $60000
            r'([0-9,]+)\s*(?:-|to|–)\s*([0-9,]+)\s*(?:per|/)',  # 50000 - 70000 per
            r'([£€₹¥])([0-9,]+)',  # £50000
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                if len(matches[0]) == 2:  # Range
                    try:
                        min_val = int(matches[0][0].replace(',', ''))
                        max_val = int(matches[0][1].replace(',', ''))
                        salary_info['salary_min'] = min_val
                        salary_info['salary_max'] = max_val
                    except ValueError:
                        continue
                else:  # Single value
                    try:
                        value = int(matches[0].replace(',', ''))
                        salary_info['salary_min'] = salary_info['salary_max'] = value
                    except ValueError:
                        continue
                break
        
        return salary_info

    def extract_skills(self, job: Dict[str, Any]) -> List[str]:
        """Extract technical skills from job description"""
        skills = []
        text = f"{job.get('title', '')} {job.get('description', '')}".lower()

        # Common technical skills
        common_skills = [
            'python', 'java', 'javascript', 'c\+\+', 'c#', 'php', 'ruby', 'go', 'rust',
            'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins',
            'git', 'linux', 'windows', 'agile', 'scrum', 'kanban',
            'machine learning', 'ai', 'data science', 'tensorflow', 'pytorch'
        ]

        for skill in common_skills:
            if skill in text:
                skills.append(skill.title())

        return list(set(skills))  # Remove duplicates

    def score_job_relevance(self, job: Dict[str, Any], search_term: str) -> float:
        """Score job relevance based on title and description match with search term"""
        score = 0.0
        search_lower = search_term.lower()
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()

        # Title matches are more important
        if search_lower in title:
            score += 1.0
            # Exact phrase match gets bonus
            if search_term.lower() in title:
                score += 0.5

        # Description matches
        if search_lower in description:
            score += 0.3

        # Skills matching search term
        skills = self.extract_skills(job)
        skill_keywords = [s.lower() for s in skills]
        if search_lower in ' '.join(skill_keywords):
            score += 0.2

        return min(score, 2.0)  # Cap at 2.0

    def enrich_jobs(self, jobs: List[Dict[str, Any]], search_term: str) -> List[Dict[str, Any]]:
        """Enrich jobs with additional metadata"""
        enriched_jobs = []

        for job in jobs:
            try:
                # Add salary information
                job['salary_info'] = self.extract_salary_info(job)

                # Add extracted skills
                job['skills'] = self.extract_skills(job)

                # Add relevance score
                job['relevance_score'] = self.score_job_relevance(job, search_term)

                # Add processing timestamp
                job['processed_at'] = datetime.now().isoformat()

                # Add job hash for tracking
                job['job_hash'] = self.generate_job_hash(job)

                enriched_jobs.append(job)
                    
            except Exception as e:
                self.logger.warning(f"Error enriching job: {e}")
                enriched_jobs.append(job)

        self.logger.info(f"Enriched {len(enriched_jobs)} jobs with metadata")
        return enriched_jobs

    def filter_jobs(self, jobs: List[Dict[str, Any]], **filters) -> List[Dict[str, Any]]:
        """Advanced job filtering"""
        filtered_jobs = jobs.copy()

        # Filter by minimum relevance score
        if 'min_relevance' in filters:
            min_score = filters['min_relevance']
            filtered_jobs = [j for j in filtered_jobs if j.get('relevance_score', 0) >= min_score]

        # Filter by required skills
        if 'required_skills' in filters:
            required = [s.lower() for s in filters['required_skills']]
            filtered_jobs = [
                j for j in filtered_jobs
                if any(skill.lower() in [s.lower() for s in j.get('skills', [])] for skill in required)
            ]

        # Filter by salary range
        if 'min_salary' in filters:
            min_salary = filters['min_salary']
            filtered_jobs = [
                j for j in filtered_jobs
                if j.get('salary_info', {}).get('salary_min') and
                j['salary_info']['salary_min'] >= min_salary
            ]

        # Filter by location keywords
        if 'location_keywords' in filters:
            keywords = [k.lower() for k in filters['location_keywords']]
            filtered_jobs = [
                j for j in filtered_jobs
                if any(kw in j.get('location', '').lower() for kw in keywords)
            ]

        # Filter by source
        if 'sources' in filters:
            sources = [s.lower() for s in filters['sources']]
            filtered_jobs = [
                j for j in filtered_jobs
                if j.get('source', '').lower() in sources
            ]

        self.logger.info(f"Filtered {len(jobs)} -> {len(filtered_jobs)} jobs")
        return filtered_jobs

    def export_jobs(self, jobs: List[Dict[str, Any]], filename: str, format: str = 'json'):
        """Export jobs to various formats"""
        if not jobs:
            self.logger.warning("No jobs to export")
            return

        try:
            if format.lower() == 'json':
                with open(f"{filename}.json", 'w', encoding='utf-8') as f:
                    json.dump(jobs, f, ensure_ascii=False, indent=2, default=str)
            elif format.lower() == 'csv':
                df = pd.DataFrame(jobs)
                # Flatten nested dicts for CSV
                if 'salary_info' in df.columns:
                    salary_df = pd.json_normalize(df['salary_info'])
                    salary_df.columns = [f"salary_{col}" for col in salary_df.columns]
                    df = pd.concat([df.drop('salary_info', axis=1), salary_df], axis=1)
                if 'skills' in df.columns:
                    df['skills'] = df['skills'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))
                df.to_csv(f"{filename}.csv", index=False, encoding='utf-8')
            elif format.lower() == 'excel':
                df = pd.DataFrame(jobs)
                df.to_excel(f"{filename}.xlsx", index=False, engine='openpyxl')

            self.logger.info(f"Exported {len(jobs)} jobs to {filename}.{format}")

        except Exception as e:
            self.logger.error(f"Error exporting jobs: {e}")

    def get_cache_key(self, search_term: str, location: str, **params) -> str:
        """Generate cache key for search parameters"""
        key_data = f"{search_term}|{location}|{str(sorted(params.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def load_from_cache(self, cache_key: str, max_age_hours: int = 24) -> Optional[List[Dict[str, Any]]]:
        """Load jobs from cache if not expired"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        if not os.path.exists(cache_file):
            return None

        # Check if cache is expired
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if file_age > timedelta(hours=max_age_hours):
            self.logger.info("Cache expired, will refresh")
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                self.logger.info(f"Loaded {len(cached_data)} jobs from cache")
                return cached_data
        except Exception as e:
            self.logger.warning(f"Error loading cache: {e}")
            return None

    def save_to_cache(self, cache_key: str, jobs: List[Dict[str, Any]]):
        """Save jobs to cache"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, ensure_ascii=False, indent=2, default=str)
            self.logger.info(f"Cached {len(jobs)} jobs")
        except Exception as e:
            self.logger.warning(f"Error saving cache: {e}")

    def scrape_with_advanced_features(self, search_term: str, location: str,
                                    use_cache: bool = True, cache_age_hours: int = 24,
                                    **scrape_params) -> List[Dict[str, Any]]:
        """
        Advanced scraping with all features: deduplication, enrichment, filtering, caching
        """
        self.logger.info(f"Starting advanced scrape for '{search_term}' in '{location}'")

        # Check cache first
        cache_key = None
        if use_cache:
            cache_key = self.get_cache_key(search_term, location, **scrape_params)
            cached_jobs = self.load_from_cache(cache_key, cache_age_hours)
            if cached_jobs:
                self.logger.info("Using cached results")
                return cached_jobs

        # Perform scraping
        start_time = datetime.now()
        raw_jobs = scrape_all(search_term, location, **scrape_params)
        scrape_time = (datetime.now() - start_time).total_seconds()

        self.logger.info(f"Scraped {len(raw_jobs)} raw jobs in {scrape_time:.2f}s")

        if not raw_jobs:
            return []

        # Process jobs through advanced pipeline
        processed_jobs = self.enrich_jobs(
            self.clean_job_data(
                self.deduplicate_jobs(raw_jobs)
            ),
            search_term
        )

        # Save to cache
        if use_cache and cache_key:
            self.save_to_cache(cache_key, processed_jobs)

        self.logger.info(f"Processed {len(processed_jobs)} jobs with advanced features")
        return processed_jobs


# Global instance for convenience
advanced_scraper = AdvancedJobScraper()


def scrape_all_advanced(job_title: str, location: str, **kwargs) -> List[Dict[str, Any]]:
    """
    Convenience function for advanced scraping
    """
    return advanced_scraper.scrape_with_advanced_features(job_title, location, **kwargs)


if __name__ == "__main__":
    # Example usage of advanced scraper
    jobs = scrape_all_advanced(
        "software engineer",
        "San Francisco, CA",
        results_wanted=50,
        linkedin_fetch_description=True
    )

    # Apply advanced filtering
    filtered_jobs = advanced_scraper.filter_jobs(
        jobs,
        min_relevance=0.5,
        required_skills=['Python', 'JavaScript'],
        sources=['indeed', 'linkedin']
    )

    # Export in multiple formats
    advanced_scraper.export_jobs(jobs, "jobs_full", "json")
    advanced_scraper.export_jobs(filtered_jobs, "jobs_filtered", "csv")

    print(f"Found {len(jobs)} jobs, {len(filtered_jobs)} after filtering")