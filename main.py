"""
Job Market Agent - Main Application
Automated job search and application pipeline with AI-powered CV tailoring
"""

# Suppress deprecation warnings FIRST, before any imports
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import sys
import json
import time
import argparse
import logging
import re
import threading
import tempfile
import traceback
import uuid
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

# Fix Windows Unicode Output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import warnings
# Suppress Appwrite SDK deprecation warnings that suggest methods not present in this version
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*list_documents.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*create_string_attribute.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*update_document.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*create_document.*")

# Third-party imports
from dotenv import load_dotenv
import pypdf
from flask import Flask, request, jsonify, send_file, g, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Appwrite imports
from appwrite.client import Client
from appwrite.services.account import Account
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.services.messaging import Messaging
from appwrite.id import ID
from appwrite.query import Query
from appwrite.input_file import InputFile
from appwrite.permission import Permission
from appwrite.role import Role

# Local imports
from agents import (
    profile_builder,
    job_intelligence,
    interview_prep_agent
)
from utils import AdvancedJobScraper, CVTailoringEngine, ApplicationTracker
from utils.scraping import extract_skills_from_description
from utils.ai_retries import retry_ai_call
from utils.pdf_generator import PDFGenerator

# Load environment variables
load_dotenv()

# Polyfill API keys if needed
if os.getenv('GOOGLE_API_KEY') and not os.getenv('GEMINI_API_KEY'):
    os.environ['GEMINI_API_KEY'] = os.getenv('GOOGLE_API_KEY')
if os.getenv('GEMINI_API_KEY') and not os.getenv('GOOGLE_API_KEY'):
    os.environ['GOOGLE_API_KEY'] = os.getenv('GEMINI_API_KEY')

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

# ==========================================
# Core Pipeline Class
# ==========================================

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
        
    def _normalize_cv_text(self, text: str) -> str:
        try:
            # Fix hyphenated line breaks: devel-\nopment -> development
            text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
            # Collapse excessive whitespace
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
            # Remove common placeholder artifacts
            text = text.replace("\x0c", "\n").strip()
        except Exception:
            pass
        return text

    def _extract_pdf_text(self, path: str) -> str:
        try:
            reader = pypdf.PdfReader(path)
            text_parts = []
            for page in reader.pages:
                t = page.extract_text() or ""
                text_parts.append(t)
            text = "\n".join(text_parts)
            if len(text.strip()) >= 200:
                return text
        except Exception as e:
            logger.warning(f"pypdf extraction failed: {e}")
        try:
            from pdfminer.high_level import extract_text as _pdfminer_extract_text  # type: ignore
            text = _pdfminer_extract_text(path) or ""
            if len(text.strip()) >= 200:
                return text
        except Exception as e:
            logger.warning(f"pdfminer extraction unavailable/failed: {e}")
        return ""

    def _extract_docx_text(self, path: str) -> str:
        try:
            import docx  # type: ignore
            doc = docx.Document(path)
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            logger.warning(f"python-docx extraction failed: {e}")
            try:
                import zipfile
                with zipfile.ZipFile(path) as z:
                    xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
                    xml = re.sub(r"<(.|\n)*?>", "\n", xml)
                    return "\n".join([l.strip() for l in xml.splitlines() if l.strip()])
            except Exception as e2:
                logger.warning(f"zip/docx fallback failed: {e2}")
        return ""

    def _extract_doc_text(self, path: str) -> str:
        try:
            import textract  # type: ignore
            return textract.process(path).decode("utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"textract .doc extraction unavailable/failed: {e}")
        return ""

    def load_cv(self):
        """Load CV content from file with robust extraction"""
        logger.info(f"Loading CV from: {self.cv_path}")
        print(f"\n📄 Loading CV from: {self.cv_path}")
        if not os.path.exists(self.cv_path):
            logger.error(f"CV not found at {self.cv_path}")
            # Raise exception or handle gracefully? 
            # In API context we might want to catch this.
            # For now keeping behavior consistent.
            raise FileNotFoundError(f"CV not found at {self.cv_path}")

        ext = Path(self.cv_path).suffix.lower()
        content = ""
        if ext == ".pdf":
            print("📄 Extracting text from PDF...")
            content = self._extract_pdf_text(self.cv_path)
        elif ext == ".docx":
            print("📄 Extracting text from DOCX...")
            content = self._extract_docx_text(self.cv_path)
        elif ext == ".doc":
            print("📄 Extracting text from DOC...")
            content = self._extract_doc_text(self.cv_path)
        else:
            try:
                with open(self.cv_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Unsupported CV format or read error: {e}")
                raise
        
        if not content or len(content.strip()) < 50:
            print("⚠️ CV text extraction weak; using minimal content placeholder")
            content = f"Extracted from {self.cv_path}: insufficient text for analysis."
        content = self._normalize_cv_text(content)
        print(f"✓ CV loaded ({len(content)} characters)")
        return content
    
    @retry_ai_call
    def build_profile(self, cv_content):
        """Build student profile using Rule-Based Parser"""
        logger.info("Building candidate profile (Rule-Based)...")
        print("\n🔍 Building candidate profile...")
        
        try:
            from utils.cv_parser import CVParser
            
            # Use file path if available and PDF, otherwise use content
            parser = None
            if self.cv_path and self.cv_path.lower().endswith('.pdf'):
                parser = CVParser(file_path=self.cv_path)
            else:
                parser = CVParser(raw_text=cv_content)
                
            cv_data = parser.parse()
            
            # Map CVData to flat profile structure
            skills = []
            if cv_data.technical_skills:
                for cat, s_list in cv_data.technical_skills.items():
                    skills.extend(s_list)
            
            # Education
            education_str = "Not specified"
            if cv_data.education:
                top_edu = cv_data.education[0]
                education_str = top_edu.degree
                if top_edu.institution:
                    education_str += f" at {top_edu.institution}"
                
            # Experience Level Heuristic from work experience
            exp_level = "Entry Level"
            if cv_data.work_experience:
                years_of_exp = len(cv_data.work_experience) * 1.5 # Rough estimate
                if any('senior' in exp.title.lower() for exp in cv_data.work_experience):
                    exp_level = "Senior"
                elif years_of_exp > 5:
                    exp_level = "Senior"
                elif years_of_exp > 2:
                    exp_level = "Mid Level"
            
            self.profile = {
                "name": cv_data.contact_info.name or "Unknown",
                "email": cv_data.contact_info.email or "",
                "phone": cv_data.contact_info.phone or "",
                "location": cv_data.contact_info.address or "",
                "skills": list(set(skills)), # Unique skills
                "experience_level": exp_level,
                "education": education_str,
                "strengths": skills[:5], # Use top skills as strengths
                "career_goals": cv_data.professional_profile or "To leverage my skills in a challenging role."
            }
            
            # Initialize CV Engine with the loaded profile
            self.cv_engine = CVTailoringEngine(cv_content, self.profile)
            
            print("✓ Profile built successfully (Rule-Based)")
            return self.profile
            
        except Exception as e:
            logger.error(f"Error building profile: {e}")
            print(f"✗ Error building profile: {e}")
            print(traceback.format_exc())
            
            # Fallback to minimal extraction
            skills = extract_skills_from_description(cv_content)
            self.profile = {
                "name": "Unknown Candidate",
                "email": "",
                "phone": "",
                "location": "",
                "skills": skills,
                "experience_level": "Entry Level",
                "education": "Not specified",
                "strengths": skills[:5],
                "career_goals": "To leverage my skills."
            }
            self.cv_engine = CVTailoringEngine(cv_content, self.profile)
            return self.profile
    
    def search_jobs(self, query, location, max_results):
        """Search for jobs using the scraper"""
        print(f"DEBUG: Entering search_jobs with query='{query}', location='{location}'")
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
                return jobs
            else:
                print("✗ No jobs found")
                return []
                
        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            print(f"✗ Error searching jobs: {e}")
            # Return empty list instead of crashing
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
        jobs = self.search_jobs(query, location, max_applications)
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


# ==========================================
# Flask API Server Setup & Helpers
# ==========================================

app = Flask(__name__)

# Configure CORS
allowed_origins = os.getenv('CORS_ORIGINS', '').split(',')
default_origins = [
    'http://localhost:5173',
    'https://job-market-agent.vercel.app',
    'https://job-market-frontend.vercel.app',
    'https://job-market-agent.onrender.com'
]
active_origins = list(set([o.strip() for o in allowed_origins + default_origins if o.strip()]))

CORS(app, resources={
    r"/api/*": {
        "origins": active_origins,
        "origin_regex": r"^https://.*\.vercel\.app$",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Appwrite-Project", "X-Appwrite-JWT"],
        "supports_credentials": True
    }
})

app.secret_key = os.getenv('SECRET_KEY') or os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Initialize Appwrite Client (Server Side Default)
client = Client()
client.set_endpoint(os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1'))
client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
# Note: set_key is not set globally for safety, but used in specific admin checks if needed.

# Configure upload folder
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'job_market_agent_uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

if not os.path.exists(UPLOAD_FOLDER):
    try:
        os.makedirs(UPLOAD_FOLDER)
    except Exception as e:
        # Fallback to local
        UPLOAD_FOLDER = 'uploads'
        if not os.path.exists(UPLOAD_FOLDER):
             os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Appwrite Constants
DATABASE_ID = 'job-market-db'
COLLECTION_ID_JOBS = 'jobs'
COLLECTION_ID_APPLICATIONS = 'applications'
COLLECTION_ID_PROFILES = 'profiles'
BUCKET_ID_CVS = 'cv-bucket'
COLLECTION_ID_ANALYTICS = 'analytics'
COLLECTION_ID_MATCHES = 'matches'

# Global storage for pipelines and profiles
store_lock = threading.Lock()
pipeline_store = {}
profile_store = {}

apply_jobs = {}
APPLY_JOB_TIMEOUT_SECS = 300
APPLY_JOB_CLEANUP_SECS = 600

rate_limits = {}
MAX_RATE_ANALYTICS_PER_MIN = 60
MAX_RATE_MATCHES_PER_MIN = 20
MAX_RATE_APPLY_PER_MIN = 5
MAX_RATE_ANALYZE_PER_MIN = 5

def check_rate(endpoint: str, limit: int, window_sec: int = 60):
    try:
        uid = getattr(g, 'user_id', None)
        if not uid:
            return True
        now = time.time()
        key = f"{uid}:{endpoint}"
        bucket = rate_limits.get(key, [])
        bucket = [t for t in bucket if now - t < window_sec]
        if len(bucket) >= limit:
            rate_limits[key] = bucket
            return False
        bucket.append(now)
        rate_limits[key] = bucket
        return True
    except Exception:
        return True

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            # Create a new client instance for this request
            request_client = Client()
            request_client.set_endpoint(os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1'))
            request_client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
            request_client.set_jwt(token)
            
            account = Account(request_client)
            user = account.get()
            
            g.user = user
            g.user_id = user['$id']
            g.client = request_client
            
        except Exception as e:
            return jsonify({'error': 'Invalid or expired token'}), 401
            
        return f(*args, **kwargs)
    return decorated_function

def parse_profile(profile_output):
    """Clean and normalize profile data"""
    # If already a clean dict from our rule-based parser, just normalize missing keys
    if isinstance(profile_output, dict):
        return {
            'name': profile_output.get('name', ''),
            'email': profile_output.get('email', ''),
            'phone': profile_output.get('phone', ''),
            'location': profile_output.get('location', ''),
            'skills': profile_output.get('skills', []),
            'experience_level': profile_output.get('experience_level', 'Entry Level'),
            'education': profile_output.get('education', ''),
            'strengths': profile_output.get('strengths', []),
            'career_goals': profile_output.get('career_goals', ''),
            'links': profile_output.get('links', {'linkedin': '', 'github': '', 'portfolio': ''})
        }

    profile_data = {'skills': [], 'experience_level': '', 'education': '', 'strengths': [], 'career_goals': '', 'name': '', 'email': '', 'phone': '', 'location': '', 'links': {'linkedin': '', 'github': '', 'portfolio': ''}}

    try:
        # Text parsing logic fallback
        profile_text = str(profile_output)
        if hasattr(profile_output, 'decode'):
            profile_text = profile_output.decode('utf-8', errors='ignore')

        json_str = profile_text
        if '```json' in profile_text:
            json_str = profile_text.split('```json')[1].split('```')[0]
        elif '```' in profile_text:
             json_str = profile_text.split('```')[1].split('```')[0]
        
        json_str = json_str.strip()
        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                return parse_profile(data)
        except Exception:
            pass

        # Regex fallback (as in api_server.py)
        
        exp_match = re.search(r'(?:Experience Level|Experience|Years)[:\s]*([^\n]+)', profile_text, re.IGNORECASE)
        if exp_match: profile_data['experience_level'] = exp_match.group(1).strip()
        
        edu_match = re.search(r'(?:Education|Qualifications|Degrees)[:\s]*([\s\S]*?)(?=\n{2,}|\n[A-Z]|$)', profile_text, re.IGNORECASE)
        if edu_match: profile_data['education'] = edu_match.group(1).strip()
        
    except Exception as e:
        print(f"Error parsing profile: {e}")
        
    return profile_data

def score_job_match(job, profile_info):
    profile_data = profile_info['profile_data']
    job_title = job.get('title', '').lower()
    job_description = (job.get('description', '') or '').lower()
    job_company = job.get('company', '').lower()
    job_text = f"{job_title} {job_description} {job_company}"
    
    score = 20
    reasons = []
    
    skills = profile_data.get('skills', [])
    matched_skills = []
    
    for skill in skills:
        skill_lower = skill.lower()
        if skill_lower in job_text:
            matched_skills.append(skill)
            score += 15
        elif any(w in job_text for w in skill_lower.split() if len(w) > 2):
            matched_skills.append(skill)
            score += 10
            
    if matched_skills:
        reasons.append(f"Matches your skills: {', '.join(matched_skills[:3])}")
        
    # Experience
    experience = profile_data.get('experience_level', '').lower()
    if experience:
        if ('senior' in experience and 'senior' in job_text) or \
           ('junior' in experience and ('junior' in job_text or 'entry' in job_text)) or \
           ('mid' in experience and ('mid' in job_text or 'intermediate' in job_text)):
             score += 15
             reasons.append("Experience level match")
    
    score = min(score, 100)
    if not reasons: reasons.append("Relevant to your profile")
    return {'score': score, 'reasons': reasons[:3]}

def send_job_match_notification(user_email, user_name, matches, threshold=70):
    try:
        high_quality = [m for m in matches if m['match_score'] >= threshold]
        if not high_quality: return
        
        high_quality.sort(key=lambda x: x['match_score'], reverse=True)
        top_matches = high_quality[:5]
        
        # Simplified email logic
        email_subject = f"🎯 {len(high_quality)} New Job Matches Found!"
        email_body = f"Hi {user_name}, checking in with {len(high_quality)} new matches!"
        
        messaging = Messaging(client)
        messaging.create_email(
            message_id=ID.unique(),
            subject=email_subject,
            content=email_body,
            targets=[user_email],
            html=False
        )
    except Exception:
        pass

def _rehydrate_pipeline_from_profile(session_id: str, client) -> JobApplicationPipeline | None:
    try:
        databases = Databases(client)
        storage = Storage(client)
        
        existing_profiles = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID_PROFILES,
            queries=[Query.equal('userId', session_id)]
        )

        if existing_profiles.get('total', 0) == 0:
            return None
        doc = existing_profiles['documents'][0]
        file_id = doc.get('cv_file_id')
        cv_text = doc.get('cv_text')
        
        if cv_text:
            pipeline = JobApplicationPipeline()
            pipeline.build_profile(cv_text)
            with store_lock:
                pipeline_store[session_id] = pipeline
                profile_store[session_id] = {
                    'profile_data': parse_profile(pipeline.profile),
                    'raw_profile': pipeline.profile,
                    'cv_filename': doc.get('cv_filename', 'CV'),
                    'cv_content': cv_text,
                    'file_id': file_id
                }
            return pipeline
        
        # Fallback download
        if file_id:
            try:
                tmp_name = f"rehydrated_{file_id}.pdf"
                cv_path = os.path.join(app.config['UPLOAD_FOLDER'], tmp_name)
                data = storage.get_file_download(bucket_id=BUCKET_ID_CVS, file_id=file_id)
                with open(cv_path, 'wb') as f:
                    f.write(data)
                
                pipeline = JobApplicationPipeline(cv_path=cv_path)
                cv_content = pipeline.load_cv()
                pipeline.build_profile(cv_content)
                with store_lock:
                    pipeline_store[session_id] = pipeline
                    profile_store[session_id] = {
                        'profile_data': parse_profile(pipeline.profile),
                        'raw_profile': pipeline.profile,
                        'cv_filename': doc.get('cv_filename', 'CV'),
                        'cv_content': cv_content,
                        'file_id': file_id
                    }
                return pipeline
            except Exception:
                pass
        return None
    except Exception:
        return None

def ensure_database_schema():
    """Ensure Appwrite schema exists."""
    try:
        api_key = os.getenv('APPWRITE_API_KEY')
        if not api_key:
            print("WARNING: APPWRITE_API_KEY not found. Schema checks skipped.")
            return

        admin_client = Client()
        admin_client.set_endpoint(os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1'))
        admin_client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
        admin_client.set_key(api_key)
        admin_db = Databases(admin_client)

        # Simplified schema check for brevity - in production keep full check
        # Ensure profiles collection has education attribute
        def _create_attr(db, db_id, coll_id, attr_id, size, required=False):
            try:
                # Using deprecated method since create_string_column doesn't exist in current SDK
                # Deprecation warnings are suppressed at module level (line 7)
                db.create_string_attribute(db_id, coll_id, attr_id, size, required)
                # Only log if it's a new attribute (not already exists)
                # print(f"✓ Added attribute '{attr_id}' to profiles")
            except Exception as e:
                # Appwrite throws 409 if attribute exists - this is expected, so we silently ignore it
                if '409' not in str(e) and 'already exists' not in str(e).lower():
                    # Only log unexpected errors
                    print(f"✗ Failed to create attribute '{attr_id}': {e}")

        try:
            _create_attr(admin_db, DATABASE_ID, COLLECTION_ID_PROFILES, 'education', 2000)
            _create_attr(admin_db, DATABASE_ID, COLLECTION_ID_PROFILES, 'experience_level', 255)
            _create_attr(admin_db, DATABASE_ID, COLLECTION_ID_PROFILES, 'career_goals', 2000)
            _create_attr(admin_db, DATABASE_ID, COLLECTION_ID_PROFILES, 'strengths', 2500) # Reduced from 10k
            _create_attr(admin_db, DATABASE_ID, COLLECTION_ID_PROFILES, 'cv_hash', 64) # SHA-256 hash

        except Exception as e:
            print(f"Schema update error: {e}")
        
        print("✓ Database schema ensured (Basic Check)")
        
    except Exception as e:
        print(f"ensure_database_schema error: {e}")

# ==========================================
# API Routes
# ==========================================

@app.route('/')
def index():
    return jsonify({
        "status": "running", 
        "message": "Job Market Agent API (Main) is active."
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/api/search-jobs', methods=['POST'])
@login_required
def search_jobs():
    try:
        data = request.get_json()
        query = data.get('query', '')
        location = data.get('location', '')
        max_results = int(data.get('max_results', 10))
        
        pipeline = JobApplicationPipeline()
        jobs = pipeline.search_jobs(query=query or DEFAULT_QUERY, location=location or DEFAULT_LOCATION, max_results=max_results)
        
        formatted_jobs = []
        for job in jobs[:10]:
            formatted_jobs.append({
                'id': str(job.get('job_hash', job.get('url', job.get('title', '')))),
                'title': job.get('title', ''),
                'company': job.get('company', ''),
                'location': job.get('location', ''),
                'description': (job.get('description', '') or '')[:200] + '...',
                'url': job.get('url', ''),
            })
        return jsonify({'jobs': formatted_jobs})
    except Exception as e:
        return jsonify({'jobs': [], 'error': str(e)})

@app.route('/api/analyze-cv', methods=['POST'])
@login_required
def analyze_cv():
    try:
        if not check_rate('analyze-cv', MAX_RATE_ANALYZE_PER_MIN):
             return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429

        cv_file = request.files.get('cv')
        overwrite = request.form.get('overwrite', 'false').lower() == 'true'
        
        if not cv_file or cv_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if cv_file and allowed_file(cv_file.filename):
            filename = secure_filename(cv_file.filename)
            cv_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Calculate file hash for duplicate detection
            import hashlib
            cv_file.seek(0)  # Reset file pointer
            file_content = cv_file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            cv_file.seek(0)  # Reset again for saving
            
            # Check for existing CV with same hash or filename
            databases = Databases(g.client)
            storage_client = Storage(g.client)
            
            existing_profiles = databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID_PROFILES,
                queries=[Query.equal('userId', g.user_id)]
            )
            
            if existing_profiles['total'] > 0:
                existing_profile = existing_profiles['documents'][0]
                existing_filename = existing_profile.get('cv_filename', '')
                existing_hash = existing_profile.get('cv_hash', '')
                existing_file_id = existing_profile.get('cv_file_id', '')
                
                # Verify the file actually exists in storage
                file_exists_in_storage = False
                if existing_file_id:
                    try:
                        storage_client.get_file(BUCKET_ID_CVS, existing_file_id)
                        file_exists_in_storage = True
                    except Exception as e:
                        logger.warning(f"File {existing_file_id} not found in storage: {e}")
                        # File is missing from storage, clean up the orphaned database record
                        try:
                            databases.delete_document(DATABASE_ID, COLLECTION_ID_PROFILES, existing_profile['$id'])
                            logger.info(f"Deleted orphaned profile record: {existing_profile['$id']}")
                        except Exception as del_err:
                            logger.error(f"Could not delete orphaned profile: {del_err}")
                
                # Only return duplicate error if file actually exists in storage
                if file_exists_in_storage:
                    # Check if same file (by hash) or same filename
                    if file_hash == existing_hash:
                        return jsonify({
                            'success': False,
                            'error': 'duplicate_exact',
                            'message': 'This exact CV file has already been uploaded.',
                            'existing_filename': existing_filename
                        }), 409
                    
                    if filename == existing_filename and not overwrite:
                        return jsonify({
                            'success': False,
                            'error': 'duplicate_filename',
                            'message': f'A CV with filename "{filename}" already exists. Do you want to replace it?',
                            'existing_filename': existing_filename
                        }), 409
                    
                    # If overwriting, delete the old file from storage first
                    if overwrite and existing_file_id:
                        try:
                            storage_client.delete_file(BUCKET_ID_CVS, existing_file_id)
                            logger.info(f"Deleted old CV file: {existing_file_id}")
                        except Exception as e:
                            logger.warning(f"Could not delete old CV file: {e}")
            
            # Save the file
            cv_file.save(cv_path)
            
            pipeline = JobApplicationPipeline(cv_path=cv_path)
            cv_content = pipeline.load_cv()
            if not cv_content:
                return jsonify({'success': False, 'error': 'Failed to load CV'})
            
            profile_text = pipeline.build_profile(cv_content)
            print("DEBUG: Returned from build_profile")
            profile_data = parse_profile(profile_text)
            print("DEBUG: Returned from parse_profile")
            
            # Appwrite Save
            try:
                databases = Databases(g.client)
                storage = Storage(g.client)
                
                logger.info(f"Saving CV file for user {g.user_id}...")
                result = storage.create_file(bucket_id=BUCKET_ID_CVS, file_id=ID.unique(), file=InputFile.from_path(cv_path))
                file_id = result['$id']
                logger.info(f"CV file saved with ID: {file_id}")

                # Update/Create Profile
                logger.info(f"Updating profile for user {g.user_id}...")
                existing_profiles = databases.list_documents(
                    database_id=DATABASE_ID,
                    collection_id=COLLECTION_ID_PROFILES,
                    queries=[Query.equal('userId', g.user_id)]
                )
                
                profile_doc_data = {
                    'userId': g.user_id,
                    'skills': json.dumps(profile_data.get('skills', [])),
                    'experience_level': profile_data.get('experience_level', 'N/A'),
                    'education': profile_data.get('education', ''),
                    'strengths': json.dumps(profile_data.get('strengths', [])),
                    'career_goals': profile_data.get('career_goals', ''),
                    'cv_file_id': file_id,
                    'cv_filename': filename,
                    'cv_hash': file_hash  # Store hash for duplicate detection
                    # Removed cv_text to save space and avoid row limits
                }

                # Retry logic for Appwrite operations (handles 502 errors)
                max_retries = 3
                retry_delay = 1
                last_error = None
                
                for attempt in range(max_retries):
                    try:
                        if existing_profiles['total'] > 0:
                            databases.update_document(DATABASE_ID, COLLECTION_ID_PROFILES, existing_profiles['documents'][0]['$id'], data=profile_doc_data)
                            logger.info("Existing profile updated.")
                        else:
                            databases.create_document(DATABASE_ID, COLLECTION_ID_PROFILES, ID.unique(), data=profile_doc_data)
                            logger.info("New profile created.")
                        break  # Success, exit retry loop
                    except Exception as retry_error:
                        last_error = retry_error
                        if attempt < max_retries - 1:
                            logger.warning(f"Appwrite operation failed (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                            import time
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            raise  # Re-raise on final attempt
                
                # Clear any existing state for this user to prevent stale data
                with store_lock:
                    # Remove old pipeline if exists
                    if g.user_id in pipeline_store:
                        del pipeline_store[g.user_id]
                    
                    # Store fresh profile data
                    profile_store[g.user_id] = {
                        'profile_data': profile_data,
                        'raw_profile': profile_text,
                        'cv_filename': filename,
                        'cv_content': cv_content,
                        'file_id': file_id,
                        'cv_hash': file_hash
                    }
                    pipeline_store[g.user_id] = pipeline

            except Exception as db_error:
                logger.error(f"Appwrite DB/Storage Error: {db_error}")
                print(f"Appwrite Error: {db_error}")
                print(traceback.format_exc())
                return jsonify({'success': False, 'error': f"Database save failed: {str(db_error)}"}), 500

            return jsonify({
                'success': True,
                'session_id': g.user_id,
                'profile': profile_data,
                'raw_profile': profile_text,
                'cv_filename': filename
            })
        
        return jsonify({'success': False, 'error': 'Invalid file type'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/profile/current', methods=['GET'])
@login_required
def get_current_profile():
    try:
        databases = Databases(g.client)
        result = databases.list_documents(DATABASE_ID, COLLECTION_ID_PROFILES, queries=[Query.equal('userId', g.user_id), Query.limit(1)])
        if result.get('total', 0) == 0:
            return jsonify({'success': False, 'error': 'No profile found'}), 404
        doc = result['documents'][0]
        return jsonify({
            'success': True, 
            'cv_filename': doc.get('cv_filename', 'Unknown'), 
            'uploaded_at': doc.get('$updatedAt', doc.get('$createdAt')), 
            'file_id': doc.get('cv_file_id')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/profile/list', methods=['GET'])
@login_required
def list_profiles():
    """List all CV profiles for the authenticated user"""
    try:
        databases = Databases(g.client)
        result = databases.list_documents(
            DATABASE_ID, 
            COLLECTION_ID_PROFILES, 
            queries=[
                Query.equal('userId', g.user_id),
                Query.order_desc('$updatedAt')
            ]
        )
        
        profiles = []
        for doc in result.get('documents', []):
            profiles.append({
                '$id': doc['$id'],
                'cv_filename': doc.get('cv_filename', 'CV.pdf'),
                'cv_file_id': doc.get('cv_file_id'),
                '$createdAt': doc.get('$createdAt'),
                '$updatedAt': doc.get('$updatedAt'),
                'experience_level': doc.get('experience_level'),
                'education': doc.get('education'),
            })
        
        return jsonify({
            'success': True,
            'profiles': profiles,
            'total': len(profiles)
        })
    except Exception as e:
        logger.error(f"Error listing profiles: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/profile/<file_id>', methods=['DELETE'])
@login_required
def delete_profile(file_id):
    """Delete a CV profile and its associated file"""
    try:
        databases = Databases(g.client)
        storage = Storage(g.client)
        
        # Find the profile document by cv_file_id
        result = databases.list_documents(
            DATABASE_ID,
            COLLECTION_ID_PROFILES,
            queries=[
                Query.equal('userId', g.user_id),
                Query.equal('cv_file_id', file_id)
            ]
        )
        
        if result.get('total', 0) == 0:
            return jsonify({
                'success': False,
                'error': 'Profile not found or access denied'
            }), 404
        
        profile_doc = result['documents'][0]
        profile_id = profile_doc['$id']
        
        # Delete the file from storage
        try:
            storage.delete_file(BUCKET_ID_CVS, file_id)
            logger.info(f"Deleted file {file_id} from storage")
        except Exception as e:
            logger.warning(f"File deletion failed (may not exist): {e}")
        
        # Delete the profile document
        databases.delete_document(
            DATABASE_ID,
            COLLECTION_ID_PROFILES,
            profile_id
        )
        logger.info(f"Deleted profile {profile_id} for user {g.user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Profile and file deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting profile: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/match-jobs', methods=['POST'])
@login_required
def match_jobs():
    print("DEBUG: Entered match_jobs endpoint")
    try:
        if not check_rate('match-jobs', MAX_RATE_MATCHES_PER_MIN):
            return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429
            
        data = request.get_json()
        print(f"DEBUG: match_jobs data received: {data}")
        location = data.get('location', DEFAULT_LOCATION)
        max_results = int(data.get('max_results', 20))
        session_id = g.user_id
        print(f"DEBUG: Session ID: {session_id}")
        
        # 1. Rehydration
        print("DEBUG: Acquiring store_lock...")
        with store_lock:
            print("DEBUG: store_lock acquired")
            pipeline = pipeline_store.get(session_id)
            if not pipeline or not pipeline.profile:
                print("DEBUG: Pipeline missing/incomplete, checking profile_store")
                profile_info = profile_store.get(session_id)
                if not profile_info:
                    print("DEBUG: profile_store miss, attempting DB rehydration")
                    # Generic rehydration
                    pipeline = _rehydrate_pipeline_from_profile(session_id, g.client)
                    if pipeline:
                         pipeline_store[session_id] = pipeline
                         if session_id in profile_store: profile_info = profile_store[session_id]
                else:
                    print("DEBUG: Found in profile_store, restoring memory")
                    # Memory restore
                    if profile_info.get('cv_content'):
                        pipeline = JobApplicationPipeline()
                        # We don't rebuild_profile necessarily to save calls, just load data
                        pipeline.profile = profile_info['raw_profile']
                        pipeline.cv_engine = CVTailoringEngine(profile_info['cv_content'], pipeline.profile)
                        pipeline_store[session_id] = pipeline
        
        print("DEBUG: Rehydration logic complete")

        if not pipeline or not pipeline.profile:
             print("DEBUG: No profile found after attempts")
             return jsonify({'success': False, 'error': 'No profile found. Please upload CV first.'})

        # 2. Search
        print("DEBUG: parsing profile...")
        profile_data = parse_profile(pipeline.profile)
        
        # Improved Query Generation - Use job titles/roles, not technical skills
        query = ""
        
        # First, try to extract a job title from career goals or professional profile
        career_goals = profile_data.get('career_goals', '')
        
        # Look for common job title patterns in career goals
        job_title_keywords = ['developer', 'engineer', 'analyst', 'manager', 'designer', 
                             'architect', 'consultant', 'specialist', 'administrator', 
                             'coordinator', 'lead', 'intern', 'graduate']
        
        if career_goals:
            career_lower = career_goals.lower()
            # Extract first sentence or phrase that contains a job title keyword
            for keyword in job_title_keywords:
                if keyword in career_lower:
                    # Extract a reasonable phrase around the keyword
                    words = career_goals.split()
                    for i, word in enumerate(words):
                        if keyword in word.lower():
                            # Take 2-3 words around the keyword
                            start = max(0, i-1)
                            end = min(len(words), i+3)
                            query = ' '.join(words[start:end])
                            break
                    if query:
                        break
        
        # If still no query, try using experience level + primary skill domain
        if not query or len(query) < 5:
            skills = profile_data.get('skills', [])
            exp_level = profile_data.get('experience_level', '')
            
            # Identify skill domain (e.g., "Web Developer" from React/JavaScript)
            skill_domains = {
                'web': ['react', 'angular', 'vue', 'html', 'css', 'javascript', 'typescript'],
                'backend': ['python', 'java', 'node', 'express', 'django', 'flask'],
                'mobile': ['react native', 'flutter', 'swift', 'kotlin', 'android', 'ios'],
                'data': ['sql', 'mongodb', 'postgresql', 'data', 'analytics'],
                'cloud': ['aws', 'azure', 'gcp', 'cloud', 'devops']
            }
            
            domain = None
            for dom, keywords in skill_domains.items():
                if any(any(kw in skill.lower() for kw in keywords) for skill in skills):
                    domain = dom
                    break
            
            # Construct query from domain + level
            if domain:
                level_prefix = ''
                if 'senior' in exp_level.lower():
                    level_prefix = 'Senior '
                elif 'junior' in exp_level.lower() or 'entry' in exp_level.lower():
                    level_prefix = 'Junior '
                
                query = f"{level_prefix}{domain.capitalize()} Developer"
            else:
                # Ultimate fallback
                query = 'Software Developer'
        
        logger.info(f"Generated job search query: {query}")
        
        jobs = pipeline.search_jobs(query, location, max_results)
        
        # 3. Match
        matches = []
        for job in jobs[:max_results]:
             match_res = score_job_match(job, {'profile_data': profile_data})
             matches.append({
                 'job': {
                    'id': str(job.get('job_hash', job.get('url', str(uuid.uuid4())))),
                    'title': job.get('title'),
                    'company': job.get('company'),
                    'location': job.get('location', location),
                    'url': job.get('url'),
                    'description': (job.get('description', '') or '')[:200]
                 },
                 'match_score': match_res['score'],
                 'match_reasons': match_res['reasons']
             })
        
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return jsonify({'success': True, 'matches': matches, 'cached': False})

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


# ==========================================
# Missing Routes Restoration
# ==========================================

def _process_application_async(job_data, session_id, client_jwt_client, template_type=None):
    try:
        if session_id not in pipeline_store:
            pipeline_store[session_id] = JobApplicationPipeline()
        pipeline = pipeline_store[session_id]
        if not getattr(pipeline, 'cv_engine', None):
            profile_info = profile_store.get(session_id)
            if profile_info and profile_info.get('cv_content'):
                from utils.cv_tailoring import CVTailoringEngine
                pipeline.cv_engine = CVTailoringEngine(
                    profile_info['cv_content'],
                    profile_info.get('profile_data', {})
                )
                pipeline.profile = profile_info.get('profile_data', {})
            else:
                rehydrated = _rehydrate_pipeline_from_profile(session_id, client_jwt_client)
                if not rehydrated:
                    if pipeline.cv_path and os.path.exists(pipeline.cv_path):
                         cv_content = pipeline.load_cv()
                         pipeline.build_profile(cv_content)  # Build profile to initialize cv_engine
                    else:
                         return {'error': 'CV not found. Please upload a CV first.'}
        app_result = pipeline.generate_application_package(job_data, template_type)
        if not app_result or not isinstance(app_result, dict):
            return {'error': 'Application generation failed. Please try a different template or re-upload your CV.'}
        interview_prep_path = pipeline.prepare_interview(job_data, output_dir=app_result.get('app_dir'))
        files_payload = {}
        try:
            databases = Databases(client_jwt_client)
            storage = Storage(client_jwt_client)
            cv_upload = storage.create_file(bucket_id=BUCKET_ID_CVS, file_id=ID.unique(), file=InputFile.from_path(app_result['cv_path']))
            cl_upload = storage.create_file(bucket_id=BUCKET_ID_CVS, file_id=ID.unique(), file=InputFile.from_path(app_result['cover_letter_path']))
            meta_upload = None
            if app_result.get('metadata_path'):
                meta_upload = storage.create_file(bucket_id=BUCKET_ID_CVS, file_id=ID.unique(), file=InputFile.from_path(app_result['metadata_path']))
            prep_upload = None
            if interview_prep_path:
                prep_upload = storage.create_file(bucket_id=BUCKET_ID_CVS, file_id=ID.unique(), file=InputFile.from_path(interview_prep_path))
            files_payload = {
                'cv': f"/api/storage/download?bucket_id={BUCKET_ID_CVS}&file_id={cv_upload['$id']}",
                'cover_letter': f"/api/storage/download?bucket_id={BUCKET_ID_CVS}&file_id={cl_upload['$id']}",
                'interview_prep': f"/api/storage/download?bucket_id={BUCKET_ID_CVS}&file_id={prep_upload['$id']}" if prep_upload else None,
                'metadata': f"/api/storage/download?bucket_id={BUCKET_ID_CVS}&file_id={meta_upload['$id']}" if meta_upload else None
            }
            databases.create_document(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID_APPLICATIONS,
                document_id=ID.unique(),
                data={
                    'userId': session_id,
                    'jobTitle': job_data.get('title', 'Unknown'),
                    'company': job_data.get('company', 'Unknown'),
                    'jobUrl': job_data.get('url', ''),
                    'location': job_data.get('location', ''),
                    'status': 'applied',
                    'files': files_payload
                }
            )
        except Exception as e:
            print(f"Error saving application to DB: {e}")
        return {'files': files_payload, 'ats_score': app_result.get('ats_score'), 'ats_analysis': app_result.get('ats_analysis')}
    except Exception as e:
        print(f"Async apply error: {e}")
        return {'error': str(e)}

@app.route('/api/apply-job', methods=['POST'])
@login_required
def apply_job():
    try:
        if not check_rate('apply-job', MAX_RATE_APPLY_PER_MIN):
            return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429
        if request.is_json:
            data = request.get_json()
            session_id = g.user_id
            job_data = data.get('job')
            template_type = data.get('template')
            job_id = str(uuid.uuid4())
            apply_jobs[job_id] = {'status': 'processing', 'created_at': time.time()}
            client_jwt_client = g.client
            def _runner():
                result = _process_application_async(job_data, session_id, client_jwt_client, template_type)
                current = apply_jobs.get(job_id, {})
                if current.get('status') == 'cancelled':
                    return
                if 'error' in result:
                    apply_jobs[job_id] = {'status': 'error', 'error': result['error'], 'created_at': current.get('created_at', time.time())}
                else:
                    apply_jobs[job_id] = {
                        'status': 'done',
                        'files': result['files'],
                        'ats': {'score': result.get('ats_score'), 'analysis': result.get('ats_analysis')},
                        'created_at': current.get('created_at', time.time())
                    }
            threading.Thread(target=_runner, daemon=True).start()
            return jsonify({'success': True, 'job_id': job_id})
        return jsonify({'success': False, 'error': 'Invalid request'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/apply-status', methods=['GET'])
@login_required
def apply_status():
    try:
        job_id = request.args.get('job_id')
        if not job_id or job_id not in apply_jobs:
            return jsonify({'status': 'not_found'})
        info = apply_jobs[job_id]
        if info.get('status') == 'processing':
            created = info.get('created_at', time.time())
            if time.time() - created > APPLY_JOB_TIMEOUT_SECS:
                info = {'status': 'error', 'error': 'Job timed out. Please try again.'}
                apply_jobs[job_id] = info
        return jsonify(info)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/api/apply-cancel', methods=['POST'])
@login_required
def apply_cancel():
    try:
        job_id = request.args.get('job_id') or (request.get_json() or {}).get('job_id')
        if not job_id or job_id not in apply_jobs:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
        info = apply_jobs[job_id]
        info['status'] = 'cancelled'
        apply_jobs[job_id] = info
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/applications', methods=['GET'])
@login_required
def get_applications():
    try:
        databases = Databases(g.client)
        try:
            page = int(request.args.get('page', '1'))
            limit = int(request.args.get('limit', '10'))
        except Exception:
            page, limit = 1, 10
        offset = max(0, (page - 1) * limit)
        result = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID_APPLICATIONS,
            queries=[
                Query.equal('userId', g.user_id),
                Query.order_desc('$createdAt'),
                Query.limit(limit),
                Query.offset(offset)
            ]
        )
        applications = []
        for doc in result['documents']:
            applications.append({
                'id': doc['$id'],
                'jobTitle': doc.get('jobTitle', 'Unknown Position'),
                'company': doc.get('company', 'Unknown Company'),
                'jobUrl': doc.get('jobUrl', ''),
                'location': doc.get('location', ''),
                'status': doc.get('status', 'applied'),
                'appliedDate': doc.get('$createdAt', '').split('T')[0],
                'files': doc.get('files')
            })
        return jsonify({'applications': applications, 'page': page, 'limit': limit, 'total': result.get('total', len(applications))})
    except Exception as e:
        return jsonify({'applications': [], 'error': str(e)})

@app.route('/api/applications/<doc_id>/status', methods=['PUT'])
@login_required
def update_application_status(doc_id):
    try:
        data = request.get_json() or {}
        new_status = data.get('status')
        allowed = {'pending', 'applied', 'interview', 'rejected'}
        if new_status not in allowed:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        databases = Databases(g.client)
        doc = databases.get_document(DATABASE_ID, COLLECTION_ID_APPLICATIONS, doc_id)
        if doc.get('userId') != g.user_id:
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
        databases.update_document(DATABASE_ID, COLLECTION_ID_APPLICATIONS, doc_id, data={'status': new_status})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/storage/download', methods=['GET'])
@login_required
def storage_download():
    """Download a file from Appwrite storage with proper headers"""
    try:
        bucket_id = request.args.get('bucket_id')
        file_id = request.args.get('file_id')
        if not bucket_id or not file_id: 
            return jsonify({'error': 'Missing bucket_id or file_id parameters'}), 400
        
        # Get file metadata first to determine filename and content type
        try:
            storage = Storage(g.client)
            file_info = storage.get_file(bucket_id, file_id)
            filename = file_info.get('name', 'download')
            
            # Determine MIME type based on file extension
            if filename.endswith('.pdf'):
                content_type = 'application/pdf'
            elif filename.endswith('.txt'):
                content_type = 'text/plain'
            elif filename.endswith('.docx'):
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif filename.endswith('.doc'):
                content_type = 'application/msword'
            else:
                content_type = 'application/octet-stream'
        except Exception as e:
            logger.error(f"Error getting file metadata: {e}")
            return jsonify({'error': 'File not found'}), 404
        
        # Stream the file download using direct API call for better performance
        endpoint = os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1')
        project_id = os.getenv('APPWRITE_PROJECT_ID')
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1] if auth_header and auth_header.startswith('Bearer ') else None
        
        if not project_id or not token: 
            return jsonify({'error': 'Storage download unavailable'}), 500
        
        url = f"{endpoint}/storage/buckets/{bucket_id}/files/{file_id}/download"
        headers = {'X-Appwrite-Project': project_id, 'X-Appwrite-JWT': token}
        
        import requests as _req
        r = _req.get(url, headers=headers, stream=True)
        
        if r.status_code != 200:
            logger.error(f"Appwrite storage download failed: {r.status_code}")
            return jsonify({'error': 'Failed to download file from storage'}), r.status_code
        
        def generate():
            for chunk in r.iter_content(chunk_size=8192):
                if chunk: 
                    yield chunk
        
        return Response(
            generate(), 
            headers={
                'Content-Type': content_type,
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        logger.error(f"Error in storage download: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics', methods=['POST'])
@login_required
def analytics():
    try:
        if not check_rate('analytics', MAX_RATE_ANALYTICS_PER_MIN):
            return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429
        data = request.get_json() or {}
        event = data.get('event')
        properties = data.get('properties', {})
        page = data.get('page')
        if not event: return jsonify({'success': False, 'error': 'Missing event'}), 400
        databases = Databases(g.client)
        databases.create_document(DATABASE_ID, COLLECTION_ID_ANALYTICS, ID.unique(), data={'userId': g.user_id, 'event': event, 'properties': json.dumps(properties), 'page': page or '', 'created_at': datetime.now().isoformat()})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/matches/last', methods=['GET'])
@login_required
def matches_last():
    try:
        databases = Databases(g.client)
        location = request.args.get('location')
        queries = [Query.equal('userId', g.user_id), Query.limit(10)]
        if location: queries.insert(1, Query.equal('location', location))
        result = databases.list_documents(DATABASE_ID, COLLECTION_ID_MATCHES, queries=queries)
        if not result or result.get('total', 0) == 0:
            return jsonify({'success': True, 'matches': [], 'cached': False})
        doc = result['documents'][0]
        matches = json.loads(doc.get('matches', '[]') or '[]')
        last_seen = datetime.now().isoformat()
        databases.update_document(DATABASE_ID, COLLECTION_ID_MATCHES, doc['$id'], data={'last_seen': last_seen})
        return jsonify({'success': True, 'matches': matches, 'location': doc.get('location', ''), 'created_at': doc.get('$createdAt'), 'last_seen': last_seen, 'cached': True})
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to fetch last matches'}), 200

@app.route('/api/profile', methods=['POST'])
@login_required
def get_profile():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        if not session_id or session_id not in profile_store:
            return jsonify({'success': False, 'error': 'No profile found'})
        profile_info = profile_store[session_id]
        return jsonify({'success': True, 'profile': profile_info['profile_data'], 'raw_profile': profile_info['raw_profile'], 'cv_filename': profile_info['cv_filename']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    try:
        data = request.get_json()
        user_id = g.user_id
        if not data: return jsonify({'success': False, 'error': 'No data'}), 400
        databases = Databases(g.client)
        existing_profiles = databases.list_documents(DATABASE_ID, COLLECTION_ID_PROFILES, queries=[Query.equal('userId', user_id)])
        profile_doc = {
            'userId': user_id,
            'skills': json.dumps(data.get('skills', [])),
            'experience_level': data.get('experience_level', ''),
            'education': data.get('education', ''),
            'strengths': json.dumps(data.get('strengths', [])),
            'career_goals': data.get('career_goals', ''),
            'notification_enabled': bool(data.get('notification_enabled', False)),
            'notification_threshold': int(data.get('notification_threshold', 70)),
            'updated_at': datetime.now().isoformat()
        }
        if existing_profiles['total'] > 0:
            databases.update_document(DATABASE_ID, COLLECTION_ID_PROFILES, existing_profiles['documents'][0]['$id'], data=profile_doc)
        else:
            databases.create_document(DATABASE_ID, COLLECTION_ID_PROFILES, ID.unique(), data=profile_doc)
        return jsonify({'success': True, 'message': 'Profile updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/profile/structured', methods=['GET'])
@login_required
def get_structured_profile():
    try:
        databases = Databases(g.client)
        result = databases.list_documents(DATABASE_ID, COLLECTION_ID_PROFILES, queries=[Query.equal('userId', g.user_id), Query.limit(10)])
        if result.get('total', 0) == 0: return jsonify({'success': False, 'error': 'No profile found'}), 404
        doc = result['documents'][0]
        def _safe_json(field, default):
            try:
                v = doc.get(field)
                if isinstance(v, str):
                    if not v.strip(): return default
                    return json.loads(v)
                return v if v is not None else default
            except Exception: return default
        profile = {
            'skills': _safe_json('skills', []),
            'experience_level': doc.get('experience_level', '') or '',
            'education': doc.get('education', '') or '',
            'strengths': _safe_json('strengths', []),
            'career_goals': doc.get('career_goals', '') or '',
            'notification_enabled': bool(doc.get('notification_enabled', False)),
            'notification_threshold': int(doc.get('notification_threshold', 70) or 70)
        }
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/apply-preview', methods=['POST'])
@login_required
def apply_preview():
    try:
        if not check_rate('apply-job', MAX_RATE_APPLY_PER_MIN): return jsonify({'success': False, 'error': 'Limit exceeded'}), 429
        data = request.get_json()
        job_data = data.get('job')
        template_type = (data.get('template') or 'MODERN').lower()
        
        with store_lock:
            if g.user_id not in pipeline_store:
                pipeline_store[g.user_id] = _rehydrate_pipeline_from_profile(g.user_id, g.client)
            pipeline = pipeline_store.get(g.user_id)
            if not pipeline: pipeline = JobApplicationPipeline(); pipeline_store[g.user_id] = pipeline
        
        if not getattr(pipeline, 'cv_engine', None):
             profile_info = profile_store.get(g.user_id)
             if profile_info and profile_info.get('cv_content'):
                 pipeline.cv_engine = CVTailoringEngine(profile_info['cv_content'], profile_info.get('profile_data', {}))
                 pipeline.profile = profile_info.get('profile_data', {})
             else:
                 return jsonify({'success': False, 'error': 'No CV found'}), 400
        
        cv_content, ats_analysis = pipeline.cv_engine.generate_tailored_cv(job_data, template_type)
        version_id = list(pipeline.cv_engine.cv_versions.keys())[-1]
        cv_data = pipeline.cv_engine.get_cv_version(version_id) or {}
        
        generator = PDFGenerator()
        header = pipeline.cv_engine._extract_header_info()
        sections = pipeline.cv_engine._build_sections(cv_data)
        cv_html = generator.generate_html(cv_content, template_name=template_type, header=header, sections=sections)
        
        cl_markdown = pipeline.cv_engine._generate_cover_letter_markdown(job_data, tailored_cv=cv_content)
        header['date'] = datetime.now().strftime('%B %d, %Y')
        cl_html = generator.generate_html(cl_markdown, template_name='cover_letter', header=header)
        
        return jsonify({'success': True, 'cv_html': cv_html, 'cover_letter_html': cl_html, 'ats': {'analysis': ats_analysis, 'score': cv_data.get('ats_score')}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/debug/cv', methods=['GET'])
@login_required
def debug_cv():
    try:
        return jsonify({'success': True, 'message': 'Debug endpoint active'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Cleanup thread
def _cleanup_apply_jobs():
    while True:
        try:
            now = time.time()
            to_delete = []
            for jid, info in list(apply_jobs.items()):
                if (now - info.get('created_at', now)) > APPLY_JOB_CLEANUP_SECS:
                    to_delete.append(jid)
            for jid in to_delete: del apply_jobs[jid]
        except Exception: pass
        time.sleep(60)

threading.Thread(target=_cleanup_apply_jobs, daemon=True).start()

# ==========================================
# Main Execution Entry Point
# ==========================================

if __name__ == "__main__":
    # Check if arguments provided
    if len(sys.argv) > 1:
        # CLI Mode
        parser = argparse.ArgumentParser(description='Job Application Pipeline')
        parser.add_argument('--cv', default=DEFAULT_CV_PATH, help='Path to CV PDF')
        parser.add_argument('--query', default=DEFAULT_QUERY, help='Job search query')
        parser.add_argument('--location', default=DEFAULT_LOCATION, help='Job location')
        parser.add_argument('--max', type=int, default=DEFAULT_MAX_JOBS, help='Max applications')
        parser.add_argument('--template', help='CV Template Type')
        
        args = parser.parse_args()
        
        pipeline = JobApplicationPipeline(cv_path=args.cv)
        pipeline.run(
            query=args.query,
            location=args.location,
            max_applications=args.max,
            template=args.template
        )
        pipeline.print_summary()
    else:
        # Server Mode (Default)
        print("Starting Job Market Agent API Server...")
        ensure_database_schema()
        port = int(os.environ.get('PORT', 8000))
        app.run(host='0.0.0.0', port=port, debug=True)
