"""
Job Market Agent - Automated Application Pipeline
Automatically finds jobs, generates optimized CVs and cover letters, and tracks applications.
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import pypdf

# Load environment variables
load_dotenv()

# Ensure both key names are available (some agents use GEMINI_API_KEY, others GOOGLE_API_KEY)
if os.getenv('GOOGLE_API_KEY') and not os.getenv('GEMINI_API_KEY'):
    os.environ['GEMINI_API_KEY'] = os.getenv('GOOGLE_API_KEY')
if os.getenv('GEMINI_API_KEY') and not os.getenv('GOOGLE_API_KEY'):
    os.environ['GOOGLE_API_KEY'] = os.getenv('GEMINI_API_KEY')

# Import consolidated agents
from agents import (
    profile_builder,
    job_intelligence,
    interview_prep_agent
)

# Import utilities
from utils import memory, AdvancedJobScraper, CVTailoringEngine, ApplicationTracker
from utils.scraping import extract_skills_from_description
from utils.ai_retries import retry_ai_call

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration Defaults
DEFAULT_CV_PATH = os.getenv('CV_FILE_PATH', 'cvs/CV.pdf')
DEFAULT_QUERY = os.getenv('SEARCH_QUERY', 'Python Developer')
DEFAULT_LOCATION = os.getenv('LOCATION', 'South Africa')
DEFAULT_MAX_JOBS = int(os.getenv('MAX_JOBS', '10'))

class JobApplicationPipeline:
    """
    Automated pipeline for job search and application.
    """
    
    def __init__(self, cv_path=DEFAULT_CV_PATH, output_dir='applications'):
        self.scraper = AdvancedJobScraper()
        self.cv_path = cv_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.tracker = ApplicationTracker()
        self.cv_engine = None
        self.profile = None
        self.applications = []
        
    def load_cv(self):
        """Load CV content from file"""
        logger.info(f"Loading CV from: {self.cv_path}")
        print(f"\n📄 Loading CV from: {self.cv_path}")
        
        if not os.path.exists(self.cv_path):
            logger.error(f"CV not found at {self.cv_path}")
            raise FileNotFoundError(f"CV not found at {self.cv_path}")
        
        # For PDF, just store the path; for text files, read content
        if self.cv_path.endswith('.pdf'):
            try:
                print("📄 Extracting text from PDF...")
                reader = pypdf.PdfReader(self.cv_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                print(f"✓ PDF loaded ({len(text)} characters)")
                return text
            except Exception as e:
                logger.error(f"Error reading PDF: {e}")
                print(f"✗ Error reading PDF: {e}")
                # Fallback to just returning the path if extraction fails, 
                # though this might break downstream agents expecting text.
                return f"CV file path: {self.cv_path} (Extraction failed)"
        else:
            with open(self.cv_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✓ CV loaded ({len(content)} characters)")
            return content
    
    @retry_ai_call
    def build_profile(self, cv_content):
        """Build student profile using Profile Builder agent"""
        logger.info("Building candidate profile...")
        print("\n🔍 Building candidate profile...")
        
        try:
            response = profile_builder.run(f"""
            Analyze this CV and create a comprehensive candidate profile.
            Return the response in strict JSON format with the following structure:
            {{
                "skills": ["skill1", "skill2", ...],
                "experience_level": "Senior/Mid/Junior",
                "education": "Highest degree/qualification",
                "strengths": ["strength1", "strength2", ...],
                "career_goals": "Summary of career goals"
            }}
            
            CV Content:
            {cv_content}
            """)
            
            # Parse the response to get a dictionary if possible, or just use the text
            # For CVTailoringEngine, we need a dict or string.
            self.profile = response.content
            
            # Initialize CV Engine with the loaded profile
            self.cv_engine = CVTailoringEngine(cv_content, self.profile)
            
            print("✓ Profile built successfully")
            return self.profile
            
        except Exception as e:
            logger.error(f"Error building profile: {e}")
            print(f"✗ Error building profile: {e}")
            # Fallback: build a minimal profile from CV content without AI
            skills = extract_skills_from_description(cv_content)
            fallback_profile = {
                "skills": skills,
                "experience_level": "N/A",
                "education": "",
                "strengths": [],
                "career_goals": ""
            }
            self.profile = fallback_profile
            self.cv_engine = CVTailoringEngine(cv_content, self.profile)
            print("✓ Fallback profile built from CV content")
            return self.profile
    
    def search_jobs(self, query, location, max_results):
        """Search for jobs using the scraper"""
        logger.info(f"Searching for jobs: '{query}' in {location}")
        print(f"\n🔎 Searching for jobs: '{query}' in {location}")
        
        try:
            jobs = self.scraper.scrape_jobs(
                site_name=['linkedin', 'indeed'],
                search_term=query,
                location=location,
                results_wanted=max_results,
                country_indeed=location
            )
            
            if jobs:
                print(f"✓ Found {len(jobs)} jobs")
                # Save jobs to memory
                for job in jobs:
                    try:
                        memory.save_job(job)
                    except:
                        pass
                return jobs
            else:
                print("✗ No jobs found")
                return []
                
        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            print(f"✗ Error searching jobs: {e}")
            return []
    
    def generate_application_package(self, job, template_type=None):
        """Generate optimized CV (PDF) and cover letter for a specific job"""
        job_title = job.get('title', 'Unknown Position')
        company = job.get('company', 'Unknown Company')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        app_dir_name = f"{company.replace(' ', '_').replace('/', '_')}_{job_title.replace(' ', '_').replace('/', '_')}_{timestamp}"
        app_dir = self.output_dir / app_dir_name
        app_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating application for: {job_title} at {company}")
        print(f"\n✍️  Generating application for: {job_title} at {company}")

        try:
            cv_content, ats_analysis = self.cv_engine.generate_tailored_cv(job, template_type)
            if not self.cv_engine.cv_versions:
                 logger.error("No CV versions generated")
                 return None
            version_id = list(self.cv_engine.cv_versions.keys())[-1]
            cv_data = self.cv_engine.get_cv_version(version_id) or {}

            pdf_path = self.cv_engine.export_cv(version_id, format='pdf', output_dir=str(app_dir))
            final_cv_path = app_dir / 'cv.pdf'
            try:
                os.replace(pdf_path, final_cv_path)
            except Exception:
                final_cv_path = Path(pdf_path)
            print(f"✓ CV generated: {final_cv_path}")

            cover_letter_result = self.cv_engine.generate_cover_letter(job, tailored_cv=cv_content, output_dir=str(app_dir))
            if isinstance(cover_letter_result, str) and cover_letter_result.endswith('.pdf') and os.path.exists(cover_letter_result):
                cl_temp = Path(cover_letter_result)
                final_cl_path = app_dir / 'cover_letter.pdf'
                try:
                    os.replace(cl_temp, final_cl_path)
                except Exception:
                    final_cl_path = cl_temp
                print(f"✓ Cover Letter generated: {final_cl_path}")
            else:
                final_cl_path = app_dir / 'cover_letter.txt'
                with open(final_cl_path, 'w', encoding='utf-8') as f:
                    f.write(cover_letter_result if isinstance(cover_letter_result, str) else str(cover_letter_result))
                print(f"✓ Cover Letter saved: {final_cl_path}")

            metadata = {
                'job': {
                    'title': job_title,
                    'company': company,
                    'location': job.get('location', ''),
                    'url': job.get('url', '')
                },
                'cv': {
                    'version_id': version_id,
                    'ats_analysis': ats_analysis,
                    'ats_score': cv_data.get('ats_score'),
                    'job_keywords': cv_data.get('job_keywords')
                },
                'relevance_score': job.get('relevance_score'),
                'paths': {
                    'cv': str(final_cv_path),
                    'cover_letter': str(final_cl_path)
                }
            }
            metadata_path = app_dir / 'metadata.json'
            with open(metadata_path, 'w', encoding='utf-8') as mf:
                json.dump(metadata, mf, ensure_ascii=False, indent=2, default=str)

            app_id = self.tracker.add_application(
                job_data=job,
                cv_path=str(final_cv_path),
                cover_letter_path=str(final_cl_path),
                ats_score=cv_data.get('ats_score'),
                metadata_path=str(metadata_path),
                app_dir=str(app_dir)
            )

            return {
                'job_title': job_title,
                'company': company,
                'cv_path': str(final_cv_path),
                'cover_letter_path': str(final_cl_path),
                'app_dir': str(app_dir),
                'metadata_path': str(metadata_path),
                'ats_score': cv_data.get('ats_score'),
                'ats_analysis': ats_analysis,
                'app_id': app_id
            }

        except Exception as e:
            logger.error(f"Error generating application: {e}")
            print(f"✗ Error generating application: {e}")
            return None

    def run(self, query, location, max_applications, template=None):
        """Run the full pipeline"""
        print("\n" + "=" * 80)
        print("🚀 JOB APPLICATION PIPELINE STARTED")
        print("=" * 80)
        
        # 1. Load CV
        cv_content = self.load_cv()
        
        # 2. Build Profile
        if not self.build_profile(cv_content):
            return
            
        # 3. Search Jobs
        jobs = self.search_jobs(query, location, max_applications) # Scrape max_applications directly to save time
        if not jobs:
            return
            
        # 4. Generate Applications
        print(f"\n📝 Generating applications for top {len(jobs)} jobs...")
        
        for i, job in enumerate(jobs):
            print(f"\n--- Application {i+1}/{len(jobs)} ---")
            
            app_result = self.generate_application_package(job, template_type=template)
            
            if app_result:
                self.applications.append(app_result)
                # Optional: Generate Interview Prep
                self.prepare_interview(job, output_dir=app_result['app_dir'])
                
            if i < len(jobs) - 1:
                time.sleep(2)
                
    @retry_ai_call
    def prepare_interview(self, job, output_dir=None):
        """Generate interview preparation materials for a job"""
        job_title = job.get('title', 'Unknown Position')
        company = job.get('company', 'Unknown Company')
        
        logger.info(f"Preparing interview materials for: {job_title} at {company}")
        print(f"\n🎯 Preparing interview materials for: {job_title} at {company}")
        
        try:
            # Generate interview prep using the interview_prep_agent
            response = interview_prep_agent.run(f"""
            Prepare comprehensive interview materials for this position:
            
            Job: {job_title}
            Company: {company}
            Description: {job.get('description', 'Not provided')}
            
            Generate:
            1. Likely interview questions (8-10 questions)
            2. Suggested answers based on the job requirements
            3. Questions the candidate should ask the interviewer
            4. Key topics to research about the company
            5. Technical concepts to review
            """)
            
            # Save interview prep to file
            out_dir = Path(output_dir) if output_dir else self.output_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            prep_path = out_dir / 'interview_prep.txt'
            with open(prep_path, 'w', encoding='utf-8') as f:
                f.write(response.content)
            
            print(f"✓ Interview prep saved: {prep_path}")
            return str(prep_path)
            
        except Exception as e:
            logger.error(f"Error preparing interview materials: {e}")
            print(f"✗ Error preparing interview materials: {e}")
            return None

    def print_summary(self):
        """Print pipeline summary"""
        print("\n" + "=" * 80)
        print("📊 PIPELINE SUMMARY")
        print("=" * 80)
        print(f"✓ Applications generated: {len(self.applications)}")
        print(f"✓ Output directory: {self.output_dir.absolute()}")
        
        if self.applications:
            print("\n📋 Generated Applications:")
            for i, app in enumerate(self.applications, 1):
                print(f"   {i}. {app['job_title']} at {app['company']}")
                print(f"      CV: {os.path.basename(app['cv_path'])}")
        
        print("\n" + "=" * 80)
        print("✅ PIPELINE COMPLETED")
        print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description='Automated Job Application Pipeline')
    parser.add_argument('--query', default=DEFAULT_QUERY, help='Job search query')
    parser.add_argument('--location', default=DEFAULT_LOCATION, help='Job location')
    parser.add_argument('--max', type=int, default=3, help='Max applications to generate')
    parser.add_argument('--cv', default=DEFAULT_CV_PATH, help='Path to CV file')
    parser.add_argument('--template', choices=['modern', 'professional', 'academic'], help='Force specific CV template')
    
    args = parser.parse_args()
    
    pipeline = JobApplicationPipeline(cv_path=args.cv)
    pipeline.run(
        query=args.query,
        location=args.location,
        max_applications=args.max,
        template=args.template
    )

if __name__ == "__main__":
    main()
