import json
import os
import hashlib
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from jobspy import scrape_jobs
import pandas as pd
import logging
import numpy as np
import google.genai as genai
from tqdm import tqdm

# Initialize Gemini client
client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

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
                # Handle NaN/None descriptions with proper pandas check
                description = job.get('description')
                if pd.isna(description) or description is None or str(description).strip() in ['', 'nan', 'NaN', 'None']:
                    job['description'] = f"Job description not available. {job.get('title', 'Position')} at {job.get('company', 'Company')}."
                else:
                    job['description'] = str(description).strip()

                # Clean and standardize location
                location = job.get('location', '')
                if pd.notna(location) and location:
                    location = str(location).strip()
                    location = re.sub(r'\s+', ' ', location)
                    job['location'] = location if location != 'N/A' else 'Unknown Location'
                else:
                    job['location'] = 'Unknown Location'

                # Validate and clean URL
                url = job.get('url', '').strip()
                if pd.notna(url) and url and url not in ['N/A', 'nan', 'None']:
                    if not url.startswith(('http://', 'https://')):
                        job['url'] = f"https://{url}"
                    else:
                        job['url'] = url
                else:
                    job['url'] = 'N/A'

                # Ensure required fields exist with proper defaults
                job['title'] = str(job.get('title', 'Unknown Title')).strip() or 'Unknown Title'
                job['company'] = str(job.get('company', 'Unknown Company')).strip() or 'Unknown Company'
                job.setdefault('source', 'unknown')
                
                # Clean date_posted
                date_posted = job.get('date_posted')
                if pd.notna(date_posted):
                    job['date_posted'] = str(date_posted)
                else:
                    job['date_posted'] = 'N/A'

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

        # Enhanced salary patterns
        patterns = [
            r'\$\s*([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)\s*(?:-|to|–)\s*\$?\s*([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)\s*k?',
            r'\$\s*([0-9]{1,3}(?:,?[0-9]{3})*)\s*k',  # $50k format
            r'([0-9]{1,3}(?:,?[0-9]{3})*)\s*-\s*([0-9]{1,3}(?:,?[0-9]{3})*)\s*(?:per|/)\s*(?:year|annum)',
            r'(?:£|€|₹|¥)\s*([0-9]{1,3}(?:,?[0-9]{3})*)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    if len(matches[0]) == 2 and matches[0][1]:  # Range
                        min_val = int(str(matches[0][0]).replace(',', '').replace('.', ''))
                        max_val = int(str(matches[0][1]).replace(',', '').replace('.', ''))
                        
                        # Handle 'k' notation (e.g., $50k = $50,000)
                        if 'k' in text[text.find(str(matches[0][0])):text.find(str(matches[0][0]))+20].lower():
                            min_val *= 1000
                            max_val *= 1000
                        
                        salary_info['salary_min'] = min_val
                        salary_info['salary_max'] = max_val
                    elif matches[0]:  # Single value
                        value = int(str(matches[0]).replace(',', '').replace('.', ''))
                        if 'k' in pattern or 'k' in text[text.find(str(matches[0])):text.find(str(matches[0]))+10].lower():
                            value *= 1000
                        salary_info['salary_min'] = salary_info['salary_max'] = value
                    
                    # Detect currency
                    if '£' in text:
                        salary_info['salary_currency'] = 'GBP'
                    elif '€' in text:
                        salary_info['salary_currency'] = 'EUR'
                    elif '₹' in text:
                        salary_info['salary_currency'] = 'INR'
                    
                    # Detect period
                    if any(word in text for word in ['hourly', 'per hour', '/hr']):
                        salary_info['salary_period'] = 'hourly'
                    elif any(word in text for word in ['monthly', 'per month', '/month']):
                        salary_info['salary_period'] = 'monthly'
                    
                    break
                except (ValueError, IndexError) as e:
                    self.logger.debug(f"Error parsing salary: {e}")
                    continue
        
        return salary_info

    def extract_skills(self, job: Dict[str, Any]) -> List[str]:
        """Extract technical skills from job description"""
        skills = []
        text = f"{job.get('title', '')} {job.get('description', '')}".lower()

        # Expanded technical skills dictionary
        common_skills = [
            'python', 'java', 'javascript', 'typescript', 'c\\+\\+', 'c#', 'php', 'ruby', 'go', 'rust', 'kotlin', 'swift',
            'react', 'angular', 'vue', 'svelte', 'node.js', 'express', 'django', 'flask', 'spring', 'fastapi',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra', 'dynamodb',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'github actions', 'gitlab',
            'git', 'linux', 'unix', 'windows', 'bash', 'shell scripting',
            'agile', 'scrum', 'kanban', 'jira', 'confluence',
            'machine learning', 'deep learning', 'ai', 'nlp', 'computer vision',
            'data science', 'data analysis', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
            'rest api', 'graphql', 'microservices', 'ci/cd', 'devops',
            'html', 'css', 'sass', 'tailwind', 'bootstrap',
            'api', 'rest', 'graphql', 'websockets',
            'testing', 'unit testing', 'integration testing', 'pytest', 'jest',
            'spark', 'hadoop', 'kafka', 'airflow', 'etl'
        ]

        for skill in common_skills:
            # Use word boundary for better matching
            pattern = r'\b' + skill.replace('\\', '\\\\') + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                # Format skill name properly
                skill_name = skill.replace('\\+\\+', '++').replace('\\', '')
                skills.append(skill_name.title() if skill_name.islower() else skill_name)

        return sorted(list(set(skills)))  # Remove duplicates and sort

    def score_job_relevance(self, job: Dict[str, Any], search_term: str) -> float:
        """Score job relevance based on title and description match with search term"""
        score = 0.0
        search_lower = search_term.lower()
        search_words = set(search_lower.split())
        
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()

        # Exact title match (highest score)
        if search_lower == title.strip():
            score += 2.0
        # Title contains full search term
        elif search_lower in title:
            score += 1.5
        # Title contains search words
        else:
            title_words = set(title.split())
            matching_words = search_words.intersection(title_words)
            score += len(matching_words) * 0.3

        # Description matches
        if search_lower in description:
            score += 0.4
        else:
            desc_words = set(description.split())
            matching_words = search_words.intersection(desc_words)
            score += len(matching_words) * 0.1

        # Skills matching search term
        skills = job.get('skills', [])
        if skills:
            skill_keywords = ' '.join([s.lower() for s in skills])
            if any(word in skill_keywords for word in search_words):
                score += 0.3

        return round(min(score, 3.0), 2)  # Cap at 3.0

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
                # Still add the job even if enrichment fails
                job.setdefault('salary_info', {})
                job.setdefault('skills', [])
                job.setdefault('relevance_score', 0.0)
                job['processed_at'] = datetime.now().isoformat()
                job['job_hash'] = self.generate_job_hash(job)
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
                # Handle skills column for Excel
                if 'skills' in df.columns:
                    df['skills'] = df['skills'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))
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

        # Perform scraping using jobspy directly
        start_time = datetime.now()

        # Set default parameters for jobspy
        params = {
            'search_term': search_term,
            'location': location,
            'results_wanted': scrape_params.get('results_wanted', 20),
            'hours_old': scrape_params.get('hours_old', 72),
            'site_name': scrape_params.get('site_name', ["indeed", "linkedin", "google"]),
            'country_indeed': scrape_params.get('country_indeed', 'USA'),
        }

        try:
            # Scrape jobs using jobspy
            jobs_df = scrape_jobs(**params)

            if jobs_df is None or jobs_df.empty:
                self.logger.warning("No jobs returned from scraping")
                return []

            # Convert DataFrame to list of dictionaries with CORRECT column names
            raw_jobs = []
            for _, row in jobs_df.iterrows():
                job_dict = {
                    'title': row.get('title', 'N/A'),
                    'company': row.get('company', 'N/A'),
                    'location': row.get('location', 'N/A'),
                    'url': row.get('job_url', 'N/A'),  # Correct column name
                    'description': row.get('description', ''),
                    'source': row.get('site', 'unknown'),  # Correct column name
                    'date_posted': row.get('date_posted', 'N/A'),
                    'job_type': row.get('job_type', 'N/A'),
                    'salary_source': row.get('min_amount', None),  # If available from jobspy
                }
                raw_jobs.append(job_dict)

            scrape_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Scraped {len(raw_jobs)} raw jobs in {scrape_time:.2f}s")

        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            return []

        if not raw_jobs:
            return []

        # Process jobs through advanced pipeline
        try:
            processed_jobs = self.enrich_jobs(
                self.clean_job_data(
                    self.deduplicate_jobs(raw_jobs)
                ),
                search_term
            )

            # Sort by relevance score
            processed_jobs.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        except Exception as e:
            self.logger.error(f"Error processing jobs: {e}")
            return []

        # Save to cache
        if use_cache and cache_key and processed_jobs:
            self.save_to_cache(cache_key, processed_jobs)

        self.logger.info(f"Processed {len(processed_jobs)} jobs with advanced features")
        return processed_jobs

# Global instance for convenience
advanced_scraper = AdvancedJobScraper()

# Configuration for API resilience
API_CONFIG = {
    'max_retries': int(os.getenv('API_MAX_RETRIES', '3')),
    'retry_delay_base': float(os.getenv('API_RETRY_DELAY', '2.0')),
    'timeout': int(os.getenv('API_TIMEOUT', '30')),
}

def check_api_status():
    """
    Check if the Gemini API is available and responsive
    Returns: (is_available: bool, status_message: str)
    """
    try:
        # Simple test request to check API availability
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Hello",
            config={'max_output_tokens': 10}  # Minimal response
        )
        return True, "API is available"
    except Exception as e:
        error_msg = str(e)
        if "503" in error_msg or "UNAVAILABLE" in error_msg:
            return False, "API is overloaded (503 Service Unavailable)"
        elif "429" in error_msg or "RATE_LIMIT" in error_msg:
            return False, "API rate limit exceeded"
        elif "401" in error_msg or "PERMISSION_DENIED" in error_msg:
            return False, "API authentication failed"
        else:
            return False, f"API error: {error_msg}"

def extract_skills_from_description(description):
    """
    Extract technical skills from job description using pattern matching
    No AI calls - efficient and cost-effective
    """
    if not description:
        return []

    # Expanded list of common tech skills and technologies
    common_skills = [
        # Programming Languages
        'Python', 'Java', 'JavaScript', 'C++', 'C#', 'PHP', 'Ruby', 'Go', 'Rust',
        'TypeScript', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB',

        # Web Technologies
        'HTML', 'CSS', 'React', 'Angular', 'Vue', 'Node.js', 'Express.js',
        'Django', 'Flask', 'Spring', 'ASP.NET', 'Laravel',

        # Databases
        'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQLite',
        'Cassandra', 'DynamoDB', 'Elasticsearch',

        # Cloud Platforms
        'AWS', 'Azure', 'GCP', 'Google Cloud', 'Heroku', 'DigitalOcean',

        # DevOps & Tools
        'Docker', 'Kubernetes', 'Jenkins', 'Git', 'GitHub', 'GitLab',
        'CI/CD', 'Terraform', 'Ansible', 'Linux', 'Ubuntu',

        # Data & ML
        'Machine Learning', 'AI', 'Data Science', 'Data Analysis',
        'Pandas', 'NumPy', 'TensorFlow', 'PyTorch', 'Scikit-learn',

        # Methodologies
        'Agile', 'Scrum', 'Kanban', 'TDD', 'BDD', 'DevOps', 'Microservices',

        # Other Technologies
        'REST API', 'GraphQL', 'JSON', 'XML', 'Apache', 'Nginx'
    ]

    found_skills = []
    description_lower = description.lower()

    # Look for exact matches
    for skill in common_skills:
        if skill.lower() in description_lower:
            found_skills.append(skill)

    # Look for common variations and abbreviations
    skill_variations = {
        'js': 'JavaScript',
        'py': 'Python',
        'ml': 'Machine Learning',
        'ai': 'AI',
        'k8s': 'Kubernetes',
        'nosql': 'NoSQL',
        'ci/cd': 'CI/CD',
        'aws': 'AWS',
        'gcp': 'GCP'
    }

    for abbr, full in skill_variations.items():
        if abbr in description_lower and full not in found_skills:
            found_skills.append(full)

    # Remove duplicates and return
    return list(set(found_skills))

def semantic_skill_match(student_skills, required_skills):
    """
    Simple text-based skill matching without expensive AI calls
    Performs basic string matching and synonym checking
    """
    if not student_skills or not required_skills:
        return [], 0

    # Define skill synonyms for basic semantic matching
    skill_synonyms = {
        'javascript': ['js', 'ecmascript', 'node.js', 'nodejs'],
        'python': ['py', 'django', 'flask'],
        'java': ['jvm', 'spring'],
        'sql': ['mysql', 'postgresql', 'oracle', 'database'],
        'nosql': ['mongodb', 'cassandra', 'redis'],
        'react': ['react.js', 'reactjs'],
        'angular': ['angular.js', 'angularjs'],
        'vue': ['vue.js', 'vuejs'],
        'aws': ['amazon web services', 'ec2', 's3'],
        'azure': ['microsoft azure'],
        'gcp': ['google cloud', 'google cloud platform'],
        'docker': ['container', 'kubernetes', 'k8s'],
        'git': ['version control', 'github', 'gitlab'],
        'ci/cd': ['continuous integration', 'continuous deployment', 'jenkins', 'github actions'],
        'ml': ['machine learning', 'ai', 'artificial intelligence'],
        'data science': ['data analysis', 'analytics', 'statistics']
    }

    matches = []

    # Normalize skills to lowercase for comparison
    student_lower = [skill.lower() for skill in student_skills]
    required_lower = [skill.lower() for skill in required_skills]

    for req_skill in required_skills:
        req_lower = req_skill.lower()

        # Check for exact matches first
        if req_lower in student_lower:
            matches.append({
                'required': req_skill,
                'student_has': student_skills[student_lower.index(req_lower)],
                'confidence': 1.0
            })
            continue

        # Check synonyms
        found_synonym = False
        for student_skill in student_skills:
            student_lower_skill = student_skill.lower()

            # Check if required skill has synonyms that match student skill
            if req_lower in skill_synonyms and any(syn in student_lower_skill for syn in skill_synonyms[req_lower]):
                matches.append({
                    'required': req_skill,
                    'student_has': student_skill,
                    'confidence': 0.8
                })
                found_synonym = True
                break

            # Check if student skill has synonyms that match required skill
            if student_lower_skill in skill_synonyms and any(syn in req_lower for syn in skill_synonyms[student_lower_skill]):
                matches.append({
                    'required': req_skill,
                    'student_has': student_skill,
                    'confidence': 0.8
                })
                found_synonym = True
                break

        if not found_synonym:
            # Check for partial string matches
            for student_skill in student_skills:
                if req_lower in student_skill.lower() or student_skill.lower() in req_lower:
                    matches.append({
                        'required': req_skill,
                        'student_has': student_skill,
                        'confidence': 0.6
                    })
                    break

        match_percentage = len(matches) / len(required_skills) * 100
        return matches, match_percentage

def discover_new_jobs(student_profile, location="Johannesburg", verbose=False, max_jobs=20, timeout=None):
    """
    Scrape job boards for new opportunities using jobspy library
    """
    # Use multiple search terms if available, otherwise fall back to desired_role
    search_terms = student_profile.get('search_terms', [])
    if not search_terms:
        desired_role = student_profile.get('desired_role', 'software engineer')
        search_terms = [desired_role]

    if verbose:
        print(f"🔄 Starting job scraping with search terms: {search_terms}")
        print(f"   🎯 Location: {location}")

    all_jobs = []
    start_time = datetime.now()

    # Use progress bar for multiple search terms
    if len(search_terms) > 1:
        search_iterator = tqdm(search_terms, desc="🔍 Scraping job sites", unit="search")
    else:
        search_iterator = search_terms

    for search_term in search_iterator:
        # Check timeout if specified
        if timeout and (datetime.now() - start_time).seconds > timeout:
            if verbose:
                print(f"⏰ Timeout reached after {(datetime.now() - start_time).seconds} seconds")
            break
        if verbose and len(search_terms) == 1:
            print(f"   🔍 Scraping for: '{search_term}' in {location}")

        # Use the advanced scraper
        term_jobs = scrape_all_advanced(search_term, location, results_wanted=max_jobs)

        # Add search term info to jobs for tracking
        for job in term_jobs:
            job['searched_with'] = search_term

        all_jobs.extend(term_jobs)

        if verbose and len(search_terms) == 1:
            print(f"   📊 Found {len(term_jobs)} jobs for '{search_term}'")
        elif len(search_terms) > 1:
            # Update progress bar description
            search_iterator.set_postfix({"jobs_found": len(term_jobs), "total": len(all_jobs)})

        # Small delay between searches to be respectful
        if len(search_terms) > 1:
            import time
            time.sleep(1)

    # Close progress bar if it was used
    if len(search_terms) > 1:
        search_iterator.close()

    if verbose:
        print(f"📊 Scraped {len(all_jobs)} total jobs")

    # Store in ChromaDB
    if all_jobs:
        from .database import store_jobs_in_db
        store_jobs_in_db(all_jobs)
        if verbose:
            print("💾 Jobs stored in database")
    elif verbose:
        print("⚠️ No jobs scraped, skipping database storage")

    # Match against student profile
    from .matching import match_student_to_jobs
    matched_jobs = match_student_to_jobs(student_profile)

    return matched_jobs

# Extract keywords from job description
def extract_job_keywords(job_description, max_retries=None):
    """
    Extract keywords from job description using pattern matching
    No AI calls - efficient and cost-effective
    Returns structured JSON-like data with categorized keywords
    """
    if not job_description:
        return _extract_keywords_fallback("")

    import re

    # Technical skills and technologies
    technical_keywords = [
        # Programming Languages
        'Python', 'Java', 'JavaScript', 'C++', 'C#', 'PHP', 'Ruby', 'Go', 'Rust',
        'TypeScript', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB',

        # Web Technologies
        'HTML', 'CSS', 'React', 'Angular', 'Vue', 'Node.js', 'Express.js',
        'Django', 'Flask', 'Spring', 'ASP.NET', 'Laravel',

        # Databases
        'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQLite',
        'Cassandra', 'DynamoDB', 'Elasticsearch',

        # Cloud Platforms
        'AWS', 'Azure', 'GCP', 'Google Cloud', 'Heroku', 'DigitalOcean',

        # DevOps & Tools
        'Docker', 'Kubernetes', 'Jenkins', 'Git', 'GitHub', 'GitLab',
        'CI/CD', 'Terraform', 'Ansible', 'Linux', 'Ubuntu',

        # Data & ML
        'Machine Learning', 'AI', 'Data Science', 'Data Analysis',
        'Pandas', 'NumPy', 'TensorFlow', 'PyTorch', 'Scikit-learn'
    ]

    # Action verbs commonly found in job descriptions
    action_verbs = [
        'develop', 'design', 'implement', 'manage', 'analyze', 'create',
        'build', 'maintain', 'optimize', 'deploy', 'test', 'collaborate',
        'lead', 'coordinate', 'integrate', 'automate', 'document',
        'research', 'innovate', 'architect', 'engineer'
    ]

    # Soft skills and qualifications
    soft_skills = [
        'communication', 'leadership', 'teamwork', 'problem solving',
        'critical thinking', 'adaptability', 'creativity', 'empathy',
        'time management', 'project management', 'mentoring'
    ]

    description_lower = job_description.lower()

    # Extract technical skills
    found_technical = []
    for skill in technical_keywords:
        if skill.lower() in description_lower:
            found_technical.append(skill)

    # Extract action verbs
    found_verbs = []
    for verb in action_verbs:
        if verb in description_lower:
            found_verbs.append(verb)

    # Extract soft skills
    found_soft = []
    for skill in soft_skills:
        if skill in description_lower:
            found_soft.append(skill)

    # Extract years of experience
    experience_patterns = re.findall(r'(\d+\+?)\s*years?\s*(?:of\s*)?experience', description_lower, re.IGNORECASE)
    experience_years = experience_patterns if experience_patterns else []

    # Create structured response
    result = f"""
{{
  "MUST_HAVE_KEYWORDS": {{
    "technical_skills": {found_technical[:12]},
    "certifications_and_qualifications": [],
    "years_of_experience": {experience_years},
    "industry_specific_terms": []
  }},
  "NICE_TO_HAVE_KEYWORDS": {{
    "soft_skills": {found_soft[:6]},
    "preferred_qualifications": [],
    "domain_knowledge": []
  }},
  "ACTION_VERBS": {found_verbs[:10]},
  "KEYWORD_VARIATIONS": {{
    "note": "Keywords extracted using efficient pattern matching without AI calls."
  }}
}}
"""

    return result

def _extract_keywords_fallback(job_description):
    """
    Fallback keyword extraction when API is unavailable
    Uses simple pattern matching and common keywords
    """
    import re

    # Common technical keywords
    common_tech_keywords = [
        'Python', 'Java', 'JavaScript', 'C++', 'C#', 'SQL', 'NoSQL',
        'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask',
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
        'Machine Learning', 'AI', 'Data Science', 'Data Analysis',
        'Git', 'Agile', 'Scrum', 'CI/CD', 'DevOps'
    ]

    # Common action verbs
    action_verbs = [
        'develop', 'design', 'implement', 'manage', 'analyze', 'create',
        'build', 'maintain', 'optimize', 'deploy', 'test', 'collaborate',
        'lead', 'coordinate', 'integrate', 'automate', 'document'
    ]

    # Extract found keywords
    found_tech = []
    found_verbs = []

    desc_lower = job_description.lower()

    for keyword in common_tech_keywords:
        if keyword.lower() in desc_lower:
            found_tech.append(keyword)

    for verb in action_verbs:
        if verb in desc_lower:
            found_verbs.append(verb)

    # Extract years of experience patterns
    experience_patterns = re.findall(r'(\d+\+?)\s*years?\s*(?:of\s*)?experience', desc_lower, re.IGNORECASE)
    experience = experience_patterns if experience_patterns else []

    fallback_result = f"""
{{
  "MUST_HAVE_KEYWORDS": {{
    "technical_skills": {found_tech[:10]},
    "certifications_and_qualifications": [],
    "years_of_experience": {experience},
    "industry_specific_terms": []
  }},
  "NICE_TO_HAVE_KEYWORDS": {{
    "soft_skills": [],
    "preferred_qualifications": [],
    "domain_knowledge": []
  }},
  "ACTION_VERBS": {found_verbs[:8]},
  "KEYWORD_VARIATIONS": {{
    "note": "This is a fallback extraction due to API unavailability. Results may be less comprehensive."
  }}
}}
"""

    return fallback_result

# Match student CV against job keywords
def keyword_gap_analysis(student_cv, job_keywords, max_retries=None):
    """
    Identify missing keywords and suggest where to add them
    Uses efficient text matching without expensive AI calls
    """
    if not student_cv or not job_keywords:
        return _gap_analysis_fallback(student_cv or "", job_keywords or "")

    import re
    import json

    try:
        # Parse job keywords if it's JSON
        if isinstance(job_keywords, str) and job_keywords.startswith('{'):
            keywords_data = json.loads(job_keywords.replace('```json', '').replace('```', ''))
        else:
            # If not JSON, treat as plain text
            keywords_data = {"fallback": job_keywords}

        cv_lower = student_cv.lower()

        # Extract all keywords from the job keywords structure
        all_keywords = []
        if "MUST_HAVE_KEYWORDS" in keywords_data:
            for category in keywords_data["MUST_HAVE_KEYWORDS"].values():
                if isinstance(category, list):
                    all_keywords.extend(category)

        if "NICE_TO_HAVE_KEYWORDS" in keywords_data:
            for category in keywords_data["NICE_TO_HAVE_KEYWORDS"].values():
                if isinstance(category, list):
                    all_keywords.extend(category)

        if "ACTION_VERBS" in keywords_data:
            if isinstance(keywords_data["ACTION_VERBS"], list):
                all_keywords.extend(keywords_data["ACTION_VERBS"])

        # Check presence of keywords
        present_keywords = []
        missing_keywords = []

        for keyword in all_keywords:
            if isinstance(keyword, str) and len(keyword.strip()) > 0:
                if keyword.lower() in cv_lower:
                    present_keywords.append(keyword)
                else:
                    missing_keywords.append(keyword)

        # Create practical suggestions based on missing keywords
        suggestions = []

        # Group suggestions by CV section
        skill_suggestions = []
        experience_suggestions = []
        summary_suggestions = []

        for keyword in missing_keywords[:10]:  # Limit to top 10 to avoid overload
            keyword_lower = keyword.lower()

            # Suggest Skills section for technical skills
            if any(term in keyword_lower for term in ['python', 'java', 'javascript', 'sql', 'react', 'docker', 'aws', 'git']):
                skill_suggestions.append(f"• Add '{keyword}' to your Skills section")
            # Suggest Experience section for action verbs and technologies
            elif any(term in keyword_lower for term in ['develop', 'design', 'implement', 'manage', 'analyze', 'build']):
                experience_suggestions.append(f"• Incorporate '{keyword}' in your experience descriptions (e.g., 'Developed {keyword} solutions')")
            else:
                summary_suggestions.append(f"• Consider adding '{keyword}' to your professional summary if relevant")

        result = f"""
**Keyword Gap Analysis (Efficient Local Processing)**

**Keywords PRESENT in CV:**
{chr(10).join(f"✅ {kw}" for kw in present_keywords[:10])}

**Keywords MISSING from CV:**
{chr(10).join(f"❌ {kw}" for kw in missing_keywords[:10])}

**Practical Suggestions:**

**Skills Section:**
{chr(10).join(skill_suggestions[:5])}

**Experience Section:**
{chr(10).join(experience_suggestions[:5])}

**Professional Summary:**
{chr(10).join(summary_suggestions[:3])}

*Note: This analysis uses efficient pattern matching without AI calls. Focus on the top missing keywords that are most relevant to the job.*
"""

        return result

    except Exception as e:
        return f"Gap analysis failed: {e}. Raw keywords: {job_keywords[:200]}..."

def _gap_analysis_fallback(student_cv, job_keywords):
    """
    Fallback gap analysis when API is unavailable
    Uses simple text matching for basic keyword presence/absence
    """
    import re
    import json

    try:
        # Parse job keywords if it's JSON
        if isinstance(job_keywords, str) and job_keywords.startswith('{'):
            keywords_data = json.loads(job_keywords.replace('```json', '').replace('```', ''))
        else:
            # If not JSON, treat as plain text
            keywords_data = {"fallback": job_keywords}

        cv_lower = student_cv.lower()

        # Extract all keywords from the job keywords structure
        all_keywords = []
        if "MUST_HAVE_KEYWORDS" in keywords_data:
            for category in keywords_data["MUST_HAVE_KEYWORDS"].values():
                if isinstance(category, list):
                    all_keywords.extend(category)

        if "NICE_TO_HAVE_KEYWORDS" in keywords_data:
            for category in keywords_data["NICE_TO_HAVE_KEYWORDS"].values():
                if isinstance(category, list):
                    all_keywords.extend(category)

        if "ACTION_VERBS" in keywords_data:
            if isinstance(keywords_data["ACTION_VERBS"], list):
                all_keywords.extend(keywords_data["ACTION_VERBS"])

        # Check presence of keywords
        present_keywords = []
        missing_keywords = []

        for keyword in all_keywords:
            if isinstance(keyword, str) and len(keyword.strip()) > 0:
                if keyword.lower() in cv_lower:
                    present_keywords.append(keyword)
                else:
                    missing_keywords.append(keyword)

        fallback_result = f"""
**Keyword Gap Analysis (Fallback Mode)**

**Keywords PRESENT in CV:**
{chr(10).join(f"✅ {kw}" for kw in present_keywords[:10])}

**Keywords MISSING from CV:**
{chr(10).join(f"❌ {kw}" for kw in missing_keywords[:10])}

**Basic Suggestions:**
• Add missing technical skills to the Skills section
• Include relevant keywords in project descriptions
• Consider adding keywords to your professional summary

*Note: This is a simplified analysis due to API unavailability. Full AI-powered analysis provides more detailed suggestions.*
"""

        return fallback_result

    except Exception as e:
        return f"Fallback analysis failed: {e}. Raw keywords: {job_keywords[:200]}..."

def scrape_all_advanced(job_title: str, location: str, **kwargs) -> List[Dict[str, Any]]:
    """
    Convenience function for advanced scraping

    Args:
        job_title: Job title or keywords to search for
        location: Location to search in
        **kwargs: Additional parameters for scraping

    Returns:
        List of enriched job dictionaries
    """
    return advanced_scraper.scrape_with_advanced_features(job_title, location, **kwargs)

if __name__ == "__main__":
    # Example usage of advanced scraper
    print("Starting job scraping...")
    
    jobs = scrape_all_advanced(
        "software engineer",
        "San Francisco, CA",
        results_wanted=30,
        hours_old=72,
        site_name=["indeed", "linkedin", "google"]
    )

    if jobs:
        print(f"\nFound {len(jobs)} jobs total")

        # Apply advanced filtering
        filtered_jobs = advanced_scraper.filter_jobs(
            jobs,
            min_relevance=0.5,
            required_skills=['Python'],
        )

        print(f"After filtering: {len(filtered_jobs)} jobs")

        # Show top 5 jobs
        print("\n=== Top 5 Most Relevant Jobs ===")
        for i, job in enumerate(filtered_jobs[:5], 1):
            print(f"\n{i}. {job['title']} at {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Relevance Score: {job['relevance_score']}")
            print(f"   Skills: {', '.join(job['skills'][:5])}")
            if job['salary_info']['salary_min']:
                print(f"   Salary: ${job['salary_info']['salary_min']:,} - ${job['salary_info']['salary_max']:,}")

        # Export in multiple formats
        advanced_scraper.export_jobs(jobs, "jobs_full", "json")
        advanced_scraper.export_jobs(filtered_jobs, "jobs_filtered", "csv")
        
        print(f"\n✓ Exported jobs to files")
    else:
        print("No jobs found. Try adjusting your search parameters.")
