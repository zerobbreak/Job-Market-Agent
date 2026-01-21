import logging
import os
import re
import json
import time
import traceback
import pypdf
from pathlib import Path
from datetime import datetime
from config import Config
from agents import interview_prep_agent
from utils import AdvancedJobScraper, CVTailoringEngine
from services import job_store
from utils.pdf_generator import PDFGenerator
from utils.scraping import extract_skills_from_description
from utils.ai_retries import retry_ai_call
from services.matching_service import SemanticMatcher
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.query import Query
from appwrite.id import ID
from appwrite.client import Client
import threading
from dataclasses import asdict

logger = logging.getLogger(__name__)

# Global storage for pipelines and profiles (Cache-Aside pattern)
pipeline_store = {}
profile_store = {}
store_lock = threading.Lock()

# Initialize Matcher
matcher = SemanticMatcher()

def parse_profile(profile_output):
    """Clean and normalize profile data"""
    if isinstance(profile_output, dict):
        return {
            'name': profile_output.get('name', ''),
            'email': profile_output.get('email', ''),
            'phone': profile_output.get('phone', ''),
            'location': profile_output.get('location', ''),
            'skills': profile_output.get('skills', []),
            'experience_level': profile_output.get('experience_level', 'Entry Level'),
            'education': profile_output.get('education', []),
            'work_experience': profile_output.get('work_experience', []),
            'projects': profile_output.get('projects', []),
            'strengths': profile_output.get('strengths', []),
            'career_goals': profile_output.get('career_goals', ''),
            'links': profile_output.get('links', {'linkedin': '', 'github': '', 'portfolio': ''})
        }

    profile_data = {'skills': [], 'experience_level': '', 'education': '', 'strengths': [], 'career_goals': '', 'name': '', 'email': '', 'phone': '', 'location': '', 'links': {'linkedin': '', 'github': '', 'portfolio': ''}}
    try:
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

        # Regex fallback
        exp_match = re.search(r'(?:Experience Level|Experience|Years)[:\s]*([^\n]+)', profile_text, re.IGNORECASE)
        if exp_match: profile_data['experience_level'] = exp_match.group(1).strip()
        
        edu_match = re.search(r'(?:Education|Qualifications|Degrees)[:\s]*([\s\S]*?)(?=\n{2,}|\n[A-Z]|$)', profile_text, re.IGNORECASE)
        if edu_match: profile_data['education'] = edu_match.group(1).strip()
        
    except Exception as e:
        logger.error(f"Error parsing profile: {e}")
        
    return profile_data


def ensure_database_schema():
    """Ensure Appwrite schema exists."""
    try:
        api_key = Config.APPWRITE_API_KEY
        if not api_key:
            logger.warning("APPWRITE_API_KEY not found. Schema checks skipped.")
            return

        admin_client = Client()
        admin_client.set_endpoint(Config.APPWRITE_ENDPOINT)
        admin_client.set_project(Config.APPWRITE_PROJECT_ID)
        admin_client.set_key(api_key)
        admin_db = Databases(admin_client)

        def _create_attr(db, db_id, coll_id, attr_id, size, required=False):
            try:
                db.create_string_attribute(db_id, coll_id, attr_id, size, required)
            except Exception as e:
                if '409' not in str(e) and 'already exists' not in str(e).lower():
                    logger.error(f"Failed to create attribute '{attr_id}': {e}")

        try:
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, 'education', 2000)
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, 'experience_level', 255)
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, 'career_goals', 2000)
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, 'strengths', 2500)
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, 'cv_hash', 64)
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, 'name', 255)
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, 'email', 255)
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, 'phone', 50)
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, 'location', 255)
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, 'work_experience', 10000, False)
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_PROFILES, 'projects', 10000, False)

            # Jobs Collection Schema
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_JOBS, 'status', 50, False)
            # Integer attribute
            try:
                admin_db.create_integer_attribute(Config.DATABASE_ID, Config.COLLECTION_ID_JOBS, 'progress', False, 0, 100, 0)
            except Exception: pass

            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_JOBS, 'phase', 255, False)
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_JOBS, 'job_data', 10000, False) # JSON string
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_JOBS, 'result', 10000, False) # JSON string
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_JOBS, 'template_type', 50, False)
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_JOBS, 'user_id', 50, True)
            _create_attr(admin_db, Config.DATABASE_ID, Config.COLLECTION_ID_JOBS, 'error', 5000, False)
            
        except Exception as e:
            logger.error(f"Schema update error: {e}")
        
        logger.info("Database schema ensured (Basic Check)")
    except Exception as e:
        logger.error(f"ensure_database_schema error: {e}")

def _rehydrate_pipeline_from_profile(session_id: str, client) -> 'JobApplicationPipeline | None':
    try:
        logger.info(f"Attempting rehydration for user {session_id}")
        databases = Databases(client)
        storage = Storage(client)
        
        existing_profiles = databases.list_documents(
            database_id=Config.DATABASE_ID,
            collection_id=Config.COLLECTION_ID_PROFILES,
            queries=[Query.equal('userId', session_id)]
        )

        if existing_profiles.get('total', 0) == 0:
            logger.info("No profile document found in DB")
            return None
            
        doc = existing_profiles['documents'][0]
        file_id = doc.get('cv_file_id')
        cv_text = doc.get('cv_text')
        
        if cv_text:
            logger.info("Rehydrating from stored cv_text")
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
        
        if file_id:
            logger.info(f"Downloading CV file {file_id} for rehydration")
            try:
                tmp_dir = Config.UPLOAD_FOLDER
                os.makedirs(tmp_dir, exist_ok=True)
                tmp_name = f"rehydrated_{session_id}_{file_id}.pdf"
                cv_path = os.path.join(tmp_dir, tmp_name)
                
                # Check if file exists and is valid size (>1KB)
                if not os.path.exists(cv_path) or os.path.getsize(cv_path) < 1024:
                    logger.info(f"Starting download of file {file_id}...")
                    try:
                         data = storage.get_file_download(bucket_id=Config.BUCKET_ID_CVS, file_id=file_id)
                         with open(cv_path, 'wb') as f:
                             f.write(data)
                         logger.info(f"Download completed: {cv_path} ({os.path.getsize(cv_path)} bytes)")
                    except Exception as download_error:
                         logger.error(f"Download failed: {download_error}")
                         return None
                else:
                     logger.info(f"Using cached file: {cv_path}")
                
                pipeline = JobApplicationPipeline(cv_path=cv_path)
                logger.info("Loading CV content...")
                cv_content = pipeline.load_cv()
                logger.info("Building profile from CV...")
                pipeline.build_profile(cv_content)
                logger.info("Profile built successfully.")
                
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
            except Exception as e:
                logger.error(f"Download rehydration failed: {e}")
                logger.error(traceback.format_exc())
                
        return None
    except Exception as e:
        logger.error(f"Rehydration overall failure: {e}")
        return None

class JobApplicationPipeline:
    def __init__(self, cv_path=None, output_dir='applications'):
        self.scraper = AdvancedJobScraper()
        self.cv_path = cv_path or Config.UPLOAD_FOLDER
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
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
        if not os.path.exists(self.cv_path):
            raise FileNotFoundError(f"CV not found at {self.cv_path}")

        ext = Path(self.cv_path).suffix.lower()
        content = ""
        if ext == ".pdf":
            content = self._extract_pdf_text(self.cv_path)
        elif ext == ".docx":
            content = self._extract_docx_text(self.cv_path)
        elif ext == ".doc":
            content = self._extract_doc_text(self.cv_path)
        else:
            try:
                with open(self.cv_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Unsupported CV format or read error: {e}")
                raise
        
        if not content or len(content.strip()) < 50:
            content = f"Extracted from {self.cv_path}: insufficient text for analysis."
        content = self._normalize_cv_text(content)
        return content
    
    @retry_ai_call
    def build_profile(self, cv_content):
        """Build student profile using Hybrid AI Parser"""
        try:
            from utils.cv_parser import CVParser
            
            parser = None
            if self.cv_path and self.cv_path.lower().endswith('.pdf'):
                parser = CVParser(file_path=self.cv_path)
            else:
                parser = CVParser(raw_text=cv_content)
                
            cv_data = parser.parse()
            
            skills = []
            if cv_data.technical_skills:
                for cat, s_list in cv_data.technical_skills.items():
                    skills.extend(s_list)
            
            # Prepare structured data for frontend
            education_list = [asdict(e) for e in cv_data.education]
            experience_list = [asdict(e) for e in cv_data.work_experience]
            projects_list = [asdict(p) for p in cv_data.projects]
            
            exp_level = "Entry Level"
            if cv_data.work_experience:
                years_of_exp = len(cv_data.work_experience) * 1.5
                if any('senior' in exp.title.lower() for exp in cv_data.work_experience) or years_of_exp > 5:
                    exp_level = "Senior"
                elif years_of_exp > 2:
                    exp_level = "Mid Level"
            
            self.profile = {
                "name": cv_data.contact_info.name or "Unknown",
                "email": cv_data.contact_info.email or "",
                "phone": cv_data.contact_info.phone or "",
                "location": cv_data.contact_info.address or "",
                "skills": list(set(skills)),
                "experience_level": exp_level,
                "education": education_list,
                "work_experience": experience_list,
                "projects": projects_list,
                "strengths": skills[:5],
                "career_goals": cv_data.professional_profile or "To leverage my skills in a challenging role.",
                "links": {
                    "linkedin": cv_data.contact_info.linkedin or "",
                    "github": cv_data.contact_info.github or "",
                    "portfolio": cv_data.contact_info.portfolio or ""
                }
            }
            
            self.cv_engine = CVTailoringEngine(cv_content, self.profile)
            return self.profile
            
        except Exception as e:
            logger.error(f"Error building profile: {e}")
            skills = extract_skills_from_description(cv_content)
            self.profile = {
                "name": "Unknown",
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
        try:
            return self.scraper.scrape_jobs(
                site_name=['linkedin', 'indeed'],
                search_term=query,
                location=location,
                results_wanted=max_results,
                country_indeed=location
            )
        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            return []

    def generate_application_package(self, job, template_type=None):
        """Generate optimized CV (PDF) and cover letter for a specific job"""
        job_title = job.get('title', 'Unknown Position')
        company = job.get('company', 'Unknown Company')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        app_dir_name = f"{company.replace(' ', '_').replace('/', '_')}_{job_title.replace(' ', '_').replace('/', '_')}_{timestamp}"
        app_dir = self.output_dir / app_dir_name
        app_dir.mkdir(parents=True, exist_ok=True)

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

            cover_letter_result = self.cv_engine.generate_cover_letter(job, tailored_cv=cv_content, output_dir=str(app_dir))
            if isinstance(cover_letter_result, str) and cover_letter_result.endswith('.pdf') and os.path.exists(cover_letter_result):
                cl_temp = Path(cover_letter_result)
                final_cl_path = app_dir / 'cover_letter.pdf'
                try:
                    os.replace(cl_temp, final_cl_path)
                except Exception:
                    final_cl_path = cl_temp
            else:
                final_cl_path = app_dir / 'cover_letter.txt'
                with open(final_cl_path, 'w', encoding='utf-8') as f:
                    f.write(cover_letter_result if isinstance(cover_letter_result, str) else str(cover_letter_result))

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

            app_id = job_store.save_application(
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
            return None

    @retry_ai_call
    def prepare_interview(self, job, output_dir=None):
        """Generate interview preparation materials for a job"""
        job_title = job.get('title', 'Unknown Position')
        company = job.get('company', 'Unknown Company')
        
        try:
            response = interview_prep_agent.run(f"""
            Prepare comprehensive interview materials for this position:
            Job: {job_title}
            Company: {company}
            Description: {job.get('description', 'Not provided')}
            """)
            
            out_dir = Path(output_dir) if output_dir else self.output_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            
            prep_path = out_dir / 'interview_prep.pdf'
            try:
                generator = PDFGenerator()
                header = {'title': f"Interview Prep: {job_title}", 'company': company, 'date': datetime.now().strftime('%Y-%m-%d')}
                success = generator.generate_pdf(markdown_content=response.content, output_path=str(prep_path), template_name='modern', header=header)
                if success:
                    return str(prep_path)
            except Exception:
                pass
                
            txt_path = out_dir / 'interview_prep.txt'
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(response.content)
            return str(txt_path)
            
            return str(txt_path)
            
        except Exception as e:
            logger.error(f"Error preparing interview materials: {e}")
            return None

    def run(self, query, location, max_applications, template=None):
        """Run the full pipeline"""
        print("\n" + "=" * 80)
        print("🚀 JOB APPLICATION PIPELINE STARTED")
        print("=" * 80)
        
        cv_content = self.load_cv()
        if not self.build_profile(cv_content):
            return
            
        jobs = self.search_jobs(query, location, max_applications)
        if not jobs:
            return
            
        print(f"\n📝 Generating applications for top {len(jobs)} jobs...")
        
        for i, job in enumerate(jobs):
            print(f"\n--- Application {i+1}/{len(jobs)} ---")
            app_result = self.generate_application_package(job, template_type=template)
            
            if app_result:
                self.applications.append(app_result)
                self.prepare_interview(job, output_dir=app_result['app_dir'])
                
            if i < len(jobs) - 1:
                time.sleep(2)

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
