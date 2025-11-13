import json
import os
import hashlib
import re
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
try:
    from jobspy import scrape_jobs  # Job scraping library
    JOBSPY_AVAILABLE = True
except ImportError:
    JOBSPY_AVAILABLE = False
    print("⚠️  jobspy library not available. Job scraping will be limited.")
    def scrape_jobs(**kwargs):
        import pandas as pd
        return pd.DataFrame()
import pandas as pd
import logging

def scrape_all(job_title, location, **kwargs):
    """
    Scrape jobs using jobspy package with full parameter support

    Args:
        job_title (str): Job search term (maps to search_term)
        location (str): Location for job search
        **kwargs: Full jobspy scrape_jobs parameters:
            - site_name (list|str): Sites to scrape ["indeed", "linkedin", "google", "glassdoor", "zip_recruiter", "bayt", "bdjobs"] (default: ["indeed", "linkedin", "google", "glassdoor", "zip_recruiter"])
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

    # Set default parameters with maximum platform support
    # Includes all python-jobspy supported platforms + custom ones
    default_params = {
        'site_name': ["indeed", "linkedin", "google", "glassdoor", "zip_recruiter"],  # Core python-jobspy platforms
        'search_term': job_title,
        'location': location,
        'results_wanted': 12,  # 12 per site = ~60 total jobs from 5 platforms (manageable)
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
                                    include_career_junction: bool = False,
                                    include_dice: bool = False,
                                    include_monster: bool = False,
                                    include_flexjobs: bool = False,
                                    include_indeed_uk: bool = False,
                                    include_talent: bool = False,
                                    include_ladders: bool = False,
                                    include_linkup: bool = False,
                                    include_simplyhired: bool = False,
                                    include_workatastartup: bool = False,
                                    include_seek_au: bool = False,
                                    include_adzuna: bool = False,
                                    include_careerbuilder: bool = False,
                                    include_idealist: bool = False,
                                    include_weworkremotely: bool = False,
                                    include_clearancejobs: bool = False,
                                    include_reed_uk: bool = False,
                                    include_cv_library: bool = False,
                                    include_totaljobs: bool = False,
                                    **scrape_params) -> List[Dict[str, Any]]:
        """
        Advanced scraping with all features: deduplication, enrichment, filtering, caching
        Supports multiple custom platforms: Career Junction, Dice, Monster, FlexJobs, Indeed UK
        """
        self.logger.info(f"Starting advanced scrape for '{search_term}' in '{location}'")

        # Check cache first
        cache_key = None
        if use_cache:
            cache_key = self.get_cache_key(search_term, location,
                                         include_career_junction=include_career_junction,
                                         include_dice=include_dice,
                                         include_monster=include_monster,
                                         include_flexjobs=include_flexjobs,
                                         include_indeed_uk=include_indeed_uk,
                                         include_talent=include_talent,
                                         include_ladders=include_ladders,
                                         include_linkup=include_linkup,
                                         include_simplyhired=include_simplyhired,
                                         include_workatastartup=include_workatastartup,
                                         include_seek_au=include_seek_au,
                                         include_adzuna=include_adzuna,
                                         include_careerbuilder=include_careerbuilder,
                                         include_idealist=include_idealist,
                                         include_weworkremotely=include_weworkremotely,
                                         include_clearancejobs=include_clearancejobs,
                                         include_reed_uk=include_reed_uk,
                                         include_cv_library=include_cv_library,
                                         include_totaljobs=include_totaljobs,
                                         **scrape_params)
            cached_jobs = self.load_from_cache(cache_key, cache_age_hours)
            if cached_jobs:
                self.logger.info("Using cached results")
                return cached_jobs

        # Perform scraping
        start_time = datetime.now()
        raw_jobs = scrape_all(search_term, location, **scrape_params)

        # Add custom platform jobs if requested
        custom_jobs_count = 0

        if include_career_junction:
            self.logger.info("Including Career Junction scraping for South African jobs")
            cj_jobs = self.scrape_career_junction(search_term, location)
            raw_jobs.extend(cj_jobs)
            custom_jobs_count += len(cj_jobs)
            self.logger.info(f"Added {len(cj_jobs)} jobs from Career Junction")

        if include_dice:
            self.logger.info("Including Dice scraping for tech/IT jobs")
            dice_jobs = self.scrape_dice(search_term, location)
            raw_jobs.extend(dice_jobs)
            custom_jobs_count += len(dice_jobs)
            self.logger.info(f"Added {len(dice_jobs)} jobs from Dice")

        if include_monster:
            self.logger.info("Including Monster scraping for general jobs")
            monster_jobs = self.scrape_monster(search_term, location)
            raw_jobs.extend(monster_jobs)
            custom_jobs_count += len(monster_jobs)
            self.logger.info(f"Added {len(monster_jobs)} jobs from Monster")

        if include_flexjobs:
            self.logger.info("Including FlexJobs scraping for remote jobs")
            flex_jobs = self.scrape_flexjobs(search_term, location)
            raw_jobs.extend(flex_jobs)
            custom_jobs_count += len(flex_jobs)
            self.logger.info(f"Added {len(flex_jobs)} jobs from FlexJobs")

        if include_indeed_uk:
            self.logger.info("Including Indeed UK scraping for UK jobs")
            indeed_uk_jobs = self.scrape_indeed_uk(search_term, location)
            raw_jobs.extend(indeed_uk_jobs)
            custom_jobs_count += len(indeed_uk_jobs)
            self.logger.info(f"Added {len(indeed_uk_jobs)} jobs from Indeed UK")

        if include_talent:
            self.logger.info("Including Talent scraping for global jobs")
            talent_jobs = self.scrape_talent(search_term, location)
            raw_jobs.extend(talent_jobs)
            custom_jobs_count += len(talent_jobs)
            self.logger.info(f"Added {len(talent_jobs)} jobs from Talent")

        if include_ladders:
            self.logger.info("Including Ladders scraping for high-paying jobs")
            ladders_jobs = self.scrape_ladders(search_term, location)
            raw_jobs.extend(ladders_jobs)
            custom_jobs_count += len(ladders_jobs)
            self.logger.info(f"Added {len(ladders_jobs)} jobs from Ladders")

        if include_linkup:
            self.logger.info("Including LinkUp scraping for direct company jobs")
            linkup_jobs = self.scrape_linkup(search_term, location)
            raw_jobs.extend(linkup_jobs)
            custom_jobs_count += len(linkup_jobs)
            self.logger.info(f"Added {len(linkup_jobs)} jobs from LinkUp")

        if include_simplyhired:
            self.logger.info("Including SimplyHired scraping for general jobs")
            simplyhired_jobs = self.scrape_simplyhired(search_term, location)
            raw_jobs.extend(simplyhired_jobs)
            custom_jobs_count += len(simplyhired_jobs)
            self.logger.info(f"Added {len(simplyhired_jobs)} jobs from SimplyHired")

        if include_workatastartup:
            self.logger.info("Including WorkAtAStartup scraping for startup jobs")
            workatastartup_jobs = self.scrape_workatastartup(search_term, location)
            raw_jobs.extend(workatastartup_jobs)
            custom_jobs_count += len(workatastartup_jobs)
            self.logger.info(f"Added {len(workatastartup_jobs)} jobs from WorkAtAStartup")

        if include_seek_au:
            self.logger.info("Including Seek AU scraping for Australian jobs")
            seek_au_jobs = self.scrape_seek_au(search_term, location)
            raw_jobs.extend(seek_au_jobs)
            custom_jobs_count += len(seek_au_jobs)
            self.logger.info(f"Added {len(seek_au_jobs)} jobs from Seek AU")

        if include_adzuna:
            self.logger.info("Including Adzuna scraping for global jobs")
            adzuna_jobs = self.scrape_adzuna(search_term, location)
            raw_jobs.extend(adzuna_jobs)
            custom_jobs_count += len(adzuna_jobs)
            self.logger.info(f"Added {len(adzuna_jobs)} jobs from Adzuna")

        if include_careerbuilder:
            self.logger.info("Including CareerBuilder scraping for large job pool")
            careerbuilder_jobs = self.scrape_careerbuilder(search_term, location)
            raw_jobs.extend(careerbuilder_jobs)
            custom_jobs_count += len(careerbuilder_jobs)
            self.logger.info(f"Added {len(careerbuilder_jobs)} jobs from CareerBuilder")

        if include_idealist:
            self.logger.info("Including Idealist scraping for nonprofit jobs")
            idealist_jobs = self.scrape_idealist(search_term, location)
            raw_jobs.extend(idealist_jobs)
            custom_jobs_count += len(idealist_jobs)
            self.logger.info(f"Added {len(idealist_jobs)} jobs from Idealist")

        if include_weworkremotely:
            self.logger.info("Including WeWorkRemotely scraping for remote jobs")
            weworkremotely_jobs = self.scrape_weworkremotely(search_term, location)
            raw_jobs.extend(weworkremotely_jobs)
            custom_jobs_count += len(weworkremotely_jobs)
            self.logger.info(f"Added {len(weworkremotely_jobs)} jobs from WeWorkRemotely")

        if include_clearancejobs:
            self.logger.info("Including ClearanceJobs scraping for security clearance jobs")
            clearancejobs_jobs = self.scrape_clearancejobs(search_term, location)
            raw_jobs.extend(clearancejobs_jobs)
            custom_jobs_count += len(clearancejobs_jobs)
            self.logger.info(f"Added {len(clearancejobs_jobs)} jobs from ClearanceJobs")

        if include_reed_uk:
            self.logger.info("Including Reed UK scraping for UK recruitment")
            reed_uk_jobs = self.scrape_reed_uk(search_term, location)
            raw_jobs.extend(reed_uk_jobs)
            custom_jobs_count += len(reed_uk_jobs)
            self.logger.info(f"Added {len(reed_uk_jobs)} jobs from Reed UK")

        if include_cv_library:
            self.logger.info("Including CV-Library scraping for UK jobs")
            cv_library_jobs = self.scrape_cv_library(search_term, location)
            raw_jobs.extend(cv_library_jobs)
            custom_jobs_count += len(cv_library_jobs)
            self.logger.info(f"Added {len(cv_library_jobs)} jobs from CV-Library")

        if include_totaljobs:
            self.logger.info("Including TotalJobs scraping for UK recruitment")
            totaljobs_jobs = self.scrape_totaljobs(search_term, location)
            raw_jobs.extend(totaljobs_jobs)
            custom_jobs_count += len(totaljobs_jobs)
            self.logger.info(f"Added {len(totaljobs_jobs)} jobs from TotalJobs")

        scrape_time = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"Scraped {len(raw_jobs)} total raw jobs in {scrape_time:.2f}s ({custom_jobs_count} from custom platforms)")

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

    def scrape_career_junction(self, search_term: str, location: str = "South Africa",
                               max_jobs: int = 20) -> List[Dict[str, Any]]:
        """
        Custom scraper for Career Junction (South African job site)
        Uses requests + BeautifulSoup as fallback when Playwright unavailable
        """
        self.logger.info(f"Scraping Career Junction for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.careerjunction.co.za"

        try:
            # Try direct search URL
            search_url = f"{base_url}/jobs/results?keywords={search_term.replace(' ', '+')}"
            if location and location.lower() != "south africa":
                search_url += f"&location={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for job listings - Career Junction uses various selectors
            job_selectors = [
                '.job-item', '.vacancy-item', '.job-card',
                '[data-job-id]', '.job-listing', '.position'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    # Extract job information
                    title_elem = job_elem.select_one('h2, h3, .job-title, .position-title, .title')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer, .company-name')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, .job-location, .place')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    # Basic description from snippet
                    desc_elem = job_elem.select_one('.description, .snippet, .summary, p')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'careerjunction'
                    }

                    # Only add if we have basic info
                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from Career Junction")

        except Exception as e:
            self.logger.error(f"Error scraping Career Junction: {e}")

        return jobs

    def scrape_dice(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for Dice.com (tech/IT jobs)
        """
        self.logger.info(f"Scraping Dice for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.dice.com"

        try:
            # Dice search URL
            search_url = f"{base_url}/jobs?q={search_term.replace(' ', '+')}"
            if location:
                search_url += f"&location={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Dice uses specific selectors for job cards
            job_selectors = [
                '.card-job', '[data-cy="job-card"]', '.search-card',
                '.job-card', '[data-testid="job-card"]'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    # Extract job information from Dice
                    title_elem = job_elem.select_one('a[data-cy="card-title-link"], h5, .jobTitle, .card-title')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('[data-cy="search-result-company-name"], .company, .employer')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('[data-cy="card-location"], .location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[data-cy="card-title-link"], a[href*="jobs"]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    # Basic description from card
                    desc_elem = job_elem.select_one('.job-description, .card-summary, p')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'dice'
                    }

                    # Only add if we have basic info
                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing Dice job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from Dice")

        except Exception as e:
            self.logger.error(f"Error scraping Dice: {e}")

        return jobs

    def scrape_monster(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for Monster.com (general job board)
        """
        self.logger.info(f"Scraping Monster for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.monster.com"

        try:
            # Monster search URL
            search_url = f"{base_url}/jobs/search?q={search_term.replace(' ', '+')}"
            if location:
                search_url += f"&where={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Monster job card selectors
            job_selectors = [
                '.card-job', '[data-testid="job-card"]', '.job-card',
                '.card-content', '.job-search-card'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2, h3, .jobTitle, a[data-bypass]')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer, [data-testid="company"]')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, [data-testid="location"]')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[href*="jobs"]', title_elem if title_elem and title_elem.name == 'a' else None)
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.job-description, .summary, p')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'monster'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing Monster job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from Monster")

        except Exception as e:
            self.logger.error(f"Error scraping Monster: {e}")

        return jobs

    def scrape_flexjobs(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for FlexJobs.com (remote/flexible jobs)
        """
        self.logger.info(f"Scraping FlexJobs for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.flexjobs.com"

        try:
            # FlexJobs search URL
            search_url = f"{base_url}/search?search={search_term.replace(' ', '+')}"
            if location:
                search_url += f"&location={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # FlexJobs job selectors
            job_selectors = [
                '.job-item', '.job-card', '[data-job-id]',
                '.job-listing', '.job-row'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2, h3, .job-title, .jobTitle, a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer, .company-name')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, .job-location, .location-text')
                    job_location = location_elem.get_text(strip=True) if location_elem else "Remote"

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.description, .job-description, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'flexjobs'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing FlexJobs element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from FlexJobs")

        except Exception as e:
            self.logger.error(f"Error scraping FlexJobs: {e}")

        return jobs

    def scrape_indeed_uk(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for Indeed UK (UK-specific version)
        """
        self.logger.info(f"Scraping Indeed UK for '{search_term}' in {location}")

        jobs = []
        base_url = "https://uk.indeed.com"

        try:
            # Indeed UK search URL
            search_url = f"{base_url}/jobs?q={search_term.replace(' ', '+')}"
            if location:
                search_url += f"&l={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Indeed UK job card selectors
            job_selectors = [
                '.job_seen_beacon', '[data-jk]', '.jobsearch-ResultsList-item',
                '.cardOutline', '.jobCard'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2 a, .jobTitle a, [data-jk] a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.companyName, .companyOverviewLink, [data-testid="company-name"]')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.companyLocation, [data-testid="job-location"]')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = title_elem if title_elem and title_elem.name == 'a' else job_elem.select_one('a[href*="jk="]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.job-snippet, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'indeed_uk'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing Indeed UK job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from Indeed UK")

        except Exception as e:
            self.logger.error(f"Error scraping Indeed UK: {e}")

        return jobs

    def scrape_talent(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for Talent.com (global job listings)
        """
        self.logger.info(f"Scraping Talent for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.talent.com"

        try:
            search_url = f"{base_url}/jobs?query={search_term.replace(' ', '+')}"
            if location:
                search_url += f"&location={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            job_selectors = [
                '.job-card', '[data-jobid]', '.job-listing',
                '.card-job', '.job-item'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2, h3, .job-title, a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer, .company-name')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.description, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'talent'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing Talent job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from Talent")

        except Exception as e:
            self.logger.error(f"Error scraping Talent: {e}")

        return jobs

    def scrape_ladders(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for Ladders.com (high-paying jobs $100K+)
        """
        self.logger.info(f"Scraping Ladders for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.theladders.com"

        try:
            search_url = f"{base_url}/jobs/search?keywords={search_term.replace(' ', '+')}"
            if location:
                search_url += f"&location={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            job_selectors = [
                '.job-card', '[data-job-id]', '.job-listing',
                '.card-outline', '.job-item'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2, h3, .job-title, a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.description, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'ladders'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing Ladders job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from Ladders")

        except Exception as e:
            self.logger.error(f"Error scraping Ladders: {e}")

        return jobs

    def scrape_linkup(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for LinkUp.com (direct company job postings)
        """
        self.logger.info(f"Scraping LinkUp for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.linkup.com"

        try:
            search_url = f"{base_url}/jobs?search={search_term.replace(' ', '+')}"
            if location:
                search_url += f"&location={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            job_selectors = [
                '.job-card', '[data-jobid]', '.job-listing',
                '.card-job', '.job-item'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2, h3, .job-title, a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.description, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'linkup'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing LinkUp job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from LinkUp")

        except Exception as e:
            self.logger.error(f"Error scraping LinkUp: {e}")

        return jobs

    def scrape_simplyhired(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for SimplyHired.com (general job search)
        """
        self.logger.info(f"Scraping SimplyHired for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.simplyhired.com"

        try:
            search_url = f"{base_url}/search?q={search_term.replace(' ', '+')}"
            if location:
                search_url += f"&l={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            job_selectors = [
                '.job-card', '[data-jobid]', '.job-listing',
                '.card-job', '.job-item'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2, h3, .job-title, a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.description, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'simplyhired'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing SimplyHired job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from SimplyHired")

        except Exception as e:
            self.logger.error(f"Error scraping SimplyHired: {e}")

        return jobs

    def scrape_workatastartup(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for WorkAtAStartup.com (startup jobs)
        """
        self.logger.info(f"Scraping WorkAtAStartup for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.workatastartup.com"

        try:
            search_url = f"{base_url}/jobs?search={search_term.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            job_selectors = [
                '.job-card', '[data-job-id]', '.job-listing',
                '.card-job', '.job-item'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2, h3, .job-title, a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer, .startup-name')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else "Remote"

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.description, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'workatastartup'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing WorkAtAStartup job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from WorkAtAStartup")

        except Exception as e:
            self.logger.error(f"Error scraping WorkAtAStartup: {e}")

        return jobs

    def scrape_seek_au(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for Seek.com.au (Australian jobs)
        """
        self.logger.info(f"Scraping Seek AU for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.seek.com.au"

        try:
            search_url = f"{base_url}/jobs?keywords={search_term.replace(' ', '+')}"
            if location:
                search_url += f"&where={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            job_selectors = [
                '[data-automation="job-card"]', '.job-card', '[data-jobid]',
                '.job-listing', '.card-job'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('[data-automation="jobTitle"], h2, h3, .job-title')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('[data-automation="jobCompany"], .company, .employer')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('[data-automation="jobLocation"], .location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[href*="job/"]', '[data-automation="jobTitle"] a')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('[data-automation="jobShortDescription"], .description, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'seek_au'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing Seek AU job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from Seek AU")

        except Exception as e:
            self.logger.error(f"Error scraping Seek AU: {e}")

        return jobs

    def scrape_adzuna(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for Adzuna.com (global job search)
        """
        self.logger.info(f"Scraping Adzuna for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.adzuna.com"

        try:
            search_url = f"{base_url}/search?q={search_term.replace(' ', '+')}"
            if location:
                search_url += f"&w={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            job_selectors = [
                '.job-card', '[data-jobid]', '.job-listing',
                '.card-job', '.job-item'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2, h3, .job-title, a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.description, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'adzuna'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing Adzuna job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from Adzuna")

        except Exception as e:
            self.logger.error(f"Error scraping Adzuna: {e}")

        return jobs

    def scrape_careerbuilder(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for CareerBuilder.com (large job pool)
        """
        self.logger.info(f"Scraping CareerBuilder for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.careerbuilder.com"

        try:
            search_url = f"{base_url}/jobs?keywords={search_term.replace(' ', '+')}"
            if location:
                search_url += f"&location={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            job_selectors = [
                '.job-card', '[data-jobid]', '.job-listing',
                '.card-job', '.job-item'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2, h3, .job-title, a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.description, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'careerbuilder'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing CareerBuilder job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from CareerBuilder")

        except Exception as e:
            self.logger.error(f"Error scraping CareerBuilder: {e}")

        return jobs

    def scrape_idealist(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for Idealist.org (nonprofit/social impact jobs)
        """
        self.logger.info(f"Scraping Idealist for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.idealist.org"

        try:
            search_url = f"{base_url}/jobs/search?keywords={search_term.replace(' ', '+')}"
            if location:
                search_url += f"&location={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            job_selectors = [
                '.job-card', '[data-jobid]', '.job-listing',
                '.card-job', '.job-item'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2, h3, .job-title, a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer, .organization')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.description, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'idealist'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing Idealist job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from Idealist")

        except Exception as e:
            self.logger.error(f"Error scraping Idealist: {e}")

        return jobs

    def scrape_weworkremotely(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for WeWorkRemotely.com (remote jobs)
        """
        self.logger.info(f"Scraping WeWorkRemotely for '{search_term}' in {location}")

        jobs = []
        base_url = "https://weworkremotely.com"

        try:
            search_url = f"{base_url}/remote-jobs/search?term={search_term.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            job_selectors = [
                '.job', '.feature', '[data-jobid]',
                '.job-listing', '.card-job'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('.job-title, h2, h3, a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    # WeWorkRemotely is remote-focused
                    job_location = "Remote"

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.job-description, .summary, .details')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'weworkremotely'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing WeWorkRemotely job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from WeWorkRemotely")

        except Exception as e:
            self.logger.error(f"Error scraping WeWorkRemotely: {e}")

        return jobs

    def scrape_clearancejobs(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for ClearanceJobs.com (security clearance jobs)
        """
        self.logger.info(f"Scraping ClearanceJobs for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.clearancejobs.com"

        try:
            search_url = f"{base_url}/jobs?keywords={search_term.replace(' ', '+')}"
            if location:
                search_url += f"&location={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            job_selectors = [
                '.job-card', '[data-jobid]', '.job-listing',
                '.card-job', '.job-item'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2, h3, .job-title, a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.description, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'clearancejobs'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing ClearanceJobs job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from ClearanceJobs")

        except Exception as e:
            self.logger.error(f"Error scraping ClearanceJobs: {e}")

        return jobs

    def scrape_reed_uk(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for Reed.co.uk (UK recruitment)
        """
        self.logger.info(f"Scraping Reed UK for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.reed.co.uk"

        try:
            search_url = f"{base_url}/jobs/{search_term.replace(' ', '-')}-jobs"
            if location:
                search_url += f"-in-{location.replace(' ', '-')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            job_selectors = [
                '.job-card', '[data-jobid]', '.job-listing',
                '.card-job', '.job-item'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2, h3, .job-title, a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.description, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'reed_uk'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing Reed UK job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from Reed UK")

        except Exception as e:
            self.logger.error(f"Error scraping Reed UK: {e}")

        return jobs

    def scrape_cv_library(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for CV-Library.co.uk (UK job board)
        """
        self.logger.info(f"Scraping CV-Library for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.cv-library.co.uk"

        try:
            search_url = f"{base_url}/job/{search_term.replace(' ', '-')}-jobs"
            if location:
                search_url += f"-in-{location.replace(' ', '-')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            job_selectors = [
                '.job-card', '[data-jobid]', '.job-listing',
                '.card-job', '.job-item'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2, h3, .job-title, a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.description, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'cv_library'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing CV-Library job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from CV-Library")

        except Exception as e:
            self.logger.error(f"Error scraping CV-Library: {e}")

        return jobs

    def scrape_totaljobs(self, search_term: str, location: str = "", max_jobs: int = 15) -> List[Dict[str, Any]]:
        """
        Custom scraper for TotalJobs.com (UK recruitment platform)
        """
        self.logger.info(f"Scraping TotalJobs for '{search_term}' in {location}")

        jobs = []
        base_url = "https://www.totaljobs.com"

        try:
            search_url = f"{base_url}/jobs/{search_term.replace(' ', '-')}"
            if location:
                search_url += f"?location={location.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = requests.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            job_selectors = [
                '.job-card', '[data-jobid]', '.job-listing',
                '.card-job', '.job-item'
            ]

            job_elements = []
            for selector in job_selectors:
                elements = soup.select(selector)
                if elements:
                    job_elements = elements
                    self.logger.info(f"Found jobs using selector: {selector}")
                    break

            for job_elem in job_elements[:max_jobs]:
                try:
                    title_elem = job_elem.select_one('h2, h3, .job-title, a')
                    title = title_elem.get_text(strip=True) if title_elem else "Job Title Not Found"

                    company_elem = job_elem.select_one('.company, .employer')
                    company = company_elem.get_text(strip=True) if company_elem else "Company Not Found"

                    location_elem = job_elem.select_one('.location, .job-location')
                    job_location = location_elem.get_text(strip=True) if location_elem else location

                    link_elem = job_elem.select_one('a[href]')
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith('http'):
                        url = base_url + url if url.startswith('/') else url

                    desc_elem = job_elem.select_one('.description, .summary')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""

                    job_data = {
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': url,
                        'description': description,
                        'source': 'totaljobs'
                    }

                    if title != "Job Title Not Found" and company != "Company Not Found":
                        jobs.append(job_data)

                except Exception as e:
                    self.logger.warning(f"Error parsing TotalJobs job element: {e}")
                    continue

            self.logger.info(f"Successfully scraped {len(jobs)} jobs from TotalJobs")

        except Exception as e:
            self.logger.error(f"Error scraping TotalJobs: {e}")

        return jobs


# Global instance for convenience
advanced_scraper = AdvancedJobScraper()


def scrape_all_advanced(job_title: str, location: str,
                       include_career_junction: bool = False,
                       include_dice: bool = False,
                       include_monster: bool = False,
                       include_flexjobs: bool = False,
                       include_indeed_uk: bool = False,
                       include_talent: bool = False,
                       include_ladders: bool = False,
                       include_linkup: bool = False,
                       include_simplyhired: bool = False,
                       include_workatastartup: bool = False,
                       include_seek_au: bool = False,
                       include_adzuna: bool = False,
                       include_careerbuilder: bool = False,
                       include_idealist: bool = False,
                       include_weworkremotely: bool = False,
                       include_clearancejobs: bool = False,
                       include_reed_uk: bool = False,
                       include_cv_library: bool = False,
                       include_totaljobs: bool = False,
                       **kwargs) -> List[Dict[str, Any]]:
    """
    Convenience function for advanced scraping with comprehensive platform support

    Custom platforms (set to True to enable):
    - include_career_junction: South African jobs from Career Junction
    - include_dice: Tech/IT jobs from Dice.com
    - include_monster: General jobs from Monster.com
    - include_flexjobs: Remote jobs from FlexJobs.com
    - include_indeed_uk: UK jobs from Indeed UK
    - include_talent: Global jobs from Talent.com
    - include_ladders: High-paying jobs from Ladders.com
    - include_linkup: Direct company jobs from LinkUp.com
    - include_simplyhired: General jobs from SimplyHired.com
    - include_workatastartup: Startup jobs from WorkAtAStartup.com
    - include_seek_au: Australian jobs from Seek.com.au
    - include_adzuna: Global jobs from Adzuna.com
    - include_careerbuilder: Large job pool from CareerBuilder.com
    - include_idealist: Nonprofit jobs from Idealist.org
    - include_weworkremotely: Remote jobs from WeWorkRemotely.com
    - include_clearancejobs: Security clearance jobs from ClearanceJobs.com
    - include_reed_uk: UK recruitment from Reed.co.uk
    - include_cv_library: UK jobs from CV-Library.co.uk
    - include_totaljobs: UK recruitment from TotalJobs.com

    Note: python-jobspy platforms (Indeed, LinkedIn, Google, Glassdoor, ZipRecruiter) are always included
    """
    return advanced_scraper.scrape_with_advanced_features(
        job_title, location,
        include_career_junction=include_career_junction,
        include_dice=include_dice,
        include_monster=include_monster,
        include_flexjobs=include_flexjobs,
        include_indeed_uk=include_indeed_uk,
        include_talent=include_talent,
        include_ladders=include_ladders,
        include_linkup=include_linkup,
        include_simplyhired=include_simplyhired,
        include_workatastartup=include_workatastartup,
        include_seek_au=include_seek_au,
        include_adzuna=include_adzuna,
        include_careerbuilder=include_careerbuilder,
        include_idealist=include_idealist,
        include_weworkremotely=include_weworkremotely,
        include_clearancejobs=include_clearancejobs,
        include_reed_uk=include_reed_uk,
        include_cv_library=include_cv_library,
        include_totaljobs=include_totaljobs,
        **kwargs
    )


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