import fitz  # PyMuPDF
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os
import sys
import argparse
import uuid
from dotenv import load_dotenv

# Import agents
from agents import profile_builder, job_matcher, ats_optimizer, cv_rewriter, cover_letter_agent, interview_prep_agent

# Team functionality will be implemented as method coordination

# Import utilities
from utils import jobs_collection, store_jobs_in_db, discover_new_jobs, match_student_to_jobs, CVTailoringEngine, MockInterviewSimulator, knowledge_base, sa_customizations, ethical_guidelines

# Import advanced scraping functions from scrapper module
from scrapper import scrape_all as advanced_scrape_all

# Load environment variables
if os.path.exists('.env'):
    load_dotenv(dotenv_path='.env', override=True)

# Validate required environment variables
if not os.getenv('GOOGLE_API_KEY'):
    raise ValueError("GOOGLE_API_KEY environment variable is required. Please set it in a .env file or environment.")

# Set defaults for optional variables
if not os.getenv('CV_FILE_PATH'):
    if os.path.exists('CV.pdf'):
        os.environ['CV_FILE_PATH'] = 'CV.pdf'
    else:
        raise ValueError("CV_FILE_PATH not set and CV.pdf not found in current directory")

# Optional environment variables with defaults
CAREER_GOALS_DEFAULT = "I want to become a software engineer in fintech"

# Configure logging
import logging
logging.getLogger('google.genai').setLevel(logging.WARNING)
logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('agno').setLevel(logging.WARNING)

# Configure Gemini API for embeddings
import google.generativeai as genai
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Initialize knowledge base (this will create collections if they don't exist)
print("🧠 Initializing Knowledge Base...")
try:
    kb_stats = knowledge_base.get_all_stats()
    total_docs = sum(stats['document_count'] if stats else 0 for stats in kb_stats.values())
    print(f"✅ Knowledge Base ready with {total_docs} documents across {len(kb_stats)} sources")

    # Initialize with sample data if collections are empty
    if total_docs == 0:
        print("📚 Populating knowledge base with sample data...")
        knowledge_base.initialize_sample_data()
except Exception as e:
    print(f"⚠️ Knowledge Base initialization warning: {e}")

# Agent coordination will be handled in CareerBoostPlatform class

def generate_student_id():
    """Generate unique student ID"""
    return str(uuid.uuid4())[:8].upper()

# All utility functions have been moved to the utils package


class JobMarketAnalyzer:
    """Professional Job Market Analysis System"""

    def __init__(self, verbose=False, quiet=False):
        self.verbose = verbose
        self.quiet = quiet
        self.start_time = datetime.now()

    def log(self, message, force=False):
        """Professional logging with level control"""
        if force or (self.verbose and not self.quiet):
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")

    def print_banner(self):
        """Display professional welcome banner"""
        print("\n" + "="*70)
        print("🎯  JOB MARKET AI ANALYZER  🎯")
        print("="*70)
        print("Advanced AI-powered job matching for students and professionals")
        print("="*70)

    def print_progress(self, phase, status="IN PROGRESS"):
        """Display professional progress indicators"""
        if not self.quiet:
            print(f"\n📋 {phase}")
            print(f"   Status: {status}")

    def print_success(self, message):
        """Display success messages"""
        if not self.quiet:
            print(f"✅ {message}")

    def print_warning(self, message):
        """Display warning messages"""
        if not self.quiet:
            print(f"⚠️  {message}")

    def print_error(self, message):
        """Display error messages"""
        print(f"❌ {message}")

    def analyze_cv(self, cv_path, career_goals):
        """Analyze CV with professional output"""
        self.print_progress("CV ANALYSIS", "PROCESSING")

        try:
            # Read CV
            cv_text = ""
            num_pages = 0
            with fitz.open(cv_path) as doc:
                num_pages = len(doc)
                for page_num, page in enumerate(doc, 1):
                    cv_text += page.get_text()
                    if not self.quiet:
                        print(f"   📄 Reading page {page_num}/{num_pages}", end='\r')
            if not self.quiet:
                print(f"   📄 CV loaded: {len(cv_text)} characters from {num_pages} pages")

            # AI Analysis
            if not self.quiet:
                print("   🤖 Analyzing with AI...")
            profile_analysis = profile_builder.run(f"""
            CV Content:
            {cv_text}

            Career Goals:
            {career_goals}

            Provide:
            1. Structured profile summary
            2. Skills inventory with proficiency levels
            3. Career trajectory assessment
            4. Recommended skill development areas
            """)

            self.print_success("CV analysis completed")
            if not self.quiet:
                print("\n📊 PROFILE ANALYSIS:")
                print("-" * 50)
                print(profile_analysis.content)

            return cv_text, profile_analysis.content

        except Exception as e:
            self.print_error(f"CV analysis failed: {e}")
            return None, None

    def discover_jobs(self, student_profile):
        """Discover and scrape jobs professionally"""
        self.print_progress("JOB DISCOVERY", "SCRAPING")

        desired_role = student_profile.get('desired_role', 'Software Engineer')
        location = student_profile.get('location', 'Johannesburg')

        if not self.quiet:
            print(f"   🎯 Searching for: {desired_role}")
            print(f"   📍 Location: {location}")

        try:
            # Use discover_new_jobs with verbose control
            matched_jobs = discover_new_jobs(student_profile, location, verbose=self.verbose)

            # Get count of jobs found
            job_count = jobs_collection.count() if hasattr(jobs_collection, 'count') else len(matched_jobs)

            if job_count > 0:
                self.print_success(f"Found {job_count} job opportunities")
                self.print_success("Jobs stored and analyzed successfully")
            else:
                self.print_warning("No jobs found during scraping")

            return job_count

        except Exception as e:
            self.print_error(f"Job discovery failed: {e}")
            return 0

    def match_jobs(self, student_profile):
        """Match jobs to profile professionally"""
        self.print_progress("JOB MATCHING", "ANALYZING")

        if jobs_collection.count() == 0:
            self.print_warning("No jobs in database. Run job discovery first.")
            return []

        try:
            matched_jobs = match_student_to_jobs(student_profile)

            if matched_jobs:
                self.print_success(f"Found {len(matched_jobs)} job matches")

                if not self.quiet:
                    print("\n🏆 TOP JOB MATCHES:")
                    print("-" * 50)

                    for i, job in enumerate(matched_jobs[:5], 1):  # Show top 5
                        score = job['match_score']
                        job_id = job['job_id']

                        # Color coding for scores
                        if score >= 70:
                            status = "🟢 EXCELLENT"
                        elif score >= 50:
                            status = "🟡 GOOD"
                        else:
                            status = "🔴 CONSIDER"

                        print(f"{i}. {status} ({score:.1f}%) - {job_id}")

                        # Show brief analysis
                        analysis = job['analysis'][:150] + "..." if len(job['analysis']) > 150 else job['analysis']
                        print(f"   {analysis}\n")

            else:
                self.print_warning("No suitable job matches found")

            return matched_jobs

        except Exception as e:
            self.print_error(f"Job matching failed: {e}")
            return []

    def rewrite_cv_for_job(self, cv_text, job_description, job_title="Target Position"):
        """Rewrite CV content optimized for a specific job"""
        self.print_progress(f"CV REWRITING for {job_title}", "OPTIMIZING")

        try:
            # Use the CV rewriter agent to optimize content
            rewritten_cv = cv_rewriter.run(f"""
            Original CV Content:
            {cv_text}

            Target Job Description:
            {job_description}

            Job Title: {job_title}

            Please rewrite the CV content following these rules:
            1. Use strong action verbs
            2. Quantify achievements where possible
            3. Show impact, not just tasks
            4. Tailor language to match job description keywords
            5. Reorder experiences by relevance to this job
            6. Maintain authenticity - never fabricate experience

            Provide the rewritten CV in this structure:
            - Professional Summary (3-4 lines)
            - Experience (reordered and rewritten)
            - Skills (categorized)
            - Education (highlighting relevant coursework)
            - Projects (if applicable)
            """)

            self.print_success("CV rewritten for maximum impact")
            if not self.quiet:
                print("\n📄 OPTIMIZED CV:")
                print("-" * 50)
                print(rewritten_cv.content[:1000] + "..." if len(rewritten_cv.content) > 1000 else rewritten_cv.content)

            return rewritten_cv.content

        except Exception as e:
            self.print_error(f"CV rewriting failed: {e}")
            return None

    def create_cv_tailoring_engine(self, cv_text, student_profile):
        """
        Create a CV tailoring engine for generating job-specific CV versions
        """
        self.print_progress("CV TAILORING", "INITIALIZING ENGINE")

        try:
            tailoring_engine = CVTailoringEngine(cv_text, student_profile)
            self.print_success("CV tailoring engine created successfully")
            return tailoring_engine
        except Exception as e:
            self.print_error(f"Failed to create CV tailoring engine: {e}")
            return None

    def tailor_cv_for_job_application(self, tailoring_engine, job_posting):
        """
        Generate a tailored CV for a specific job application
        """
        job_title = job_posting.get('title', 'Position')
        company = job_posting.get('company', 'Company')

        self.print_progress(f"CV TAILORING for {company} - {job_title}", "GENERATING")

        try:
            tailored_cv, ats_analysis = tailoring_engine.generate_tailored_cv(job_posting)

            if tailored_cv:
                self.print_success(f"Tailored CV generated for {company}")
                if not self.quiet:
                    print("\n📄 TAILORED CV PREVIEW:")
                    print("-" * 50)
                    preview = tailored_cv[:500] + "..." if len(tailored_cv) > 500 else tailored_cv
                    print(preview)
                    print(f"\n📊 ATS Analysis: {ats_analysis[:200]}..." if len(ats_analysis) > 200 else ats_analysis)
            else:
                self.print_error("Failed to generate tailored CV")

            return tailored_cv, ats_analysis

        except Exception as e:
            self.print_error(f"CV tailoring failed: {e}")
            return None, None

    def generate_cover_letter(self, tailoring_engine, job_posting, tailored_cv=None):
        """
        Generate a personalized cover letter for a job application
        """
        job_title = job_posting.get('title', 'Position')
        company = job_posting.get('company', 'Company')

        self.print_progress(f"COVER LETTER for {company} - {job_title}", "GENERATING")

        try:
            cover_letter = tailoring_engine.generate_cover_letter(job_posting, tailored_cv)

            if cover_letter:
                self.print_success(f"Cover letter generated for {company}")
                if not self.quiet:
                    print("\n📝 COVER LETTER PREVIEW:")
                    print("-" * 50)
                    preview = cover_letter[:600] + "..." if len(cover_letter) > 600 else cover_letter
                    print(preview)
            else:
                self.print_error("Failed to generate cover letter")

            return cover_letter

        except Exception as e:
            self.print_error(f"Cover letter generation failed: {e}")
            return None

    def generate_interview_questions(self, tailoring_engine, job_posting, tailored_cv=None):
        """
        Generate predicted interview questions for a job application
        """
        job_title = job_posting.get('title', 'Position')
        company = job_posting.get('company', 'Company')

        self.print_progress(f"INTERVIEW PREP for {company} - {job_title}", "GENERATING QUESTIONS")

        try:
            questions = tailoring_engine.generate_interview_questions(job_posting, tailored_cv)

            if questions:
                self.print_success(f"Interview questions generated for {company}")
                if not self.quiet:
                    print("\n🎯 INTERVIEW QUESTIONS PREVIEW:")
                    print("-" * 50)
                    # Show first part of questions
                    lines = questions.split('\n')[:15]  # Show first 15 lines
                    print('\n'.join(lines))
                    if len(questions.split('\n')) > 15:
                        print("... (truncated - full list available)")
            else:
                self.print_error("Failed to generate interview questions")

            return questions

        except Exception as e:
            self.print_error(f"Interview questions generation failed: {e}")
            return None

    def create_mock_interview_simulator(self, job_role, company, student_profile=None):
        """
        Create a mock interview simulator for interview practice
        """
        self.print_progress("INTERVIEW SIMULATOR", "INITIALIZING")

        try:
            simulator = MockInterviewSimulator(job_role, company, student_profile)
            self.print_success(f"Mock interview simulator created for {job_role} at {company}")
            return simulator
        except Exception as e:
            self.print_error(f"Failed to create interview simulator: {e}")
            return None

    def conduct_mock_interview(self, simulator, student_name):
        """
        Conduct a complete mock interview session
        """
        try:
            # Start the interview
            greeting = simulator.start_interview(student_name)

            # Conduct the interview
            final_report = simulator.conduct_interview()

            # Display final report
            if final_report:
                self.print_success("Mock interview completed!")
                print("\n📊 FINAL PERFORMANCE REPORT:")
                print("=" * 60)
                print(final_report)
                print("=" * 60)

            return final_report

        except Exception as e:
            self.print_error(f"Mock interview failed: {e}")
            return None

    def conduct_mock_interview_with_copilot(self, simulator, student_name, enable_copilot=True):
        """
        Conduct a mock interview with Interview Copilot hints enabled
        """
        try:
            # Start the interview
            greeting = simulator.start_interview(student_name)

            if enable_copilot:
                print("\n⚠️  INTERVIEW COPILOT ENABLED")
                print("   🤖 You will receive subtle hints after each question")
                print("   📝 Use these as reminders, not complete answers")
                print("   🎯 Focus on your own experiences and authentic responses")
                print("="*80)

            # Conduct the interview with copilot enabled
            final_report = simulator.conduct_interview(enable_copilot=enable_copilot)

            # Display final report
            if final_report:
                self.print_success("Mock interview with copilot completed!")
                print("\n📊 FINAL PERFORMANCE REPORT:")
                print("=" * 60)
                print(final_report)
                print("=" * 60)

                if enable_copilot:
                    print("\n🤖 INTERVIEW COPILOT NOTE:")
                    print("   The hints provided were designed to help you remember key points")
                    print("   and structure your answers better. In real interviews, you would")
                    print("   not have access to these hints - practice building confidence")
                    print("   to answer questions independently.")

            return final_report

        except Exception as e:
            self.print_error(f"Mock interview with copilot failed: {e}")
            return None

    def get_interview_copilot_hint(self, question, student_profile=None):
        """
        Get a copilot hint for a specific question (for standalone use)
        """
        try:
            # Create a temporary simulator to access the copilot method
            temp_simulator = MockInterviewSimulator("Temp", "Temp", student_profile)
            hint = temp_simulator.get_interview_copilot_hint(question, student_profile)

            print("\n🤖 Interview Copilot Hint:")
            print("-" * 40)
            print(hint)
            print("-" * 40)
            print("💡 Remember: Use as subtle reminders, not complete answers")

            return hint

        except Exception as e:
            self.print_error(f"Failed to get copilot hint: {e}")
            return None

    def run_analysis(self, cv_path, career_goals=None):
        """Run complete analysis pipeline"""
        # Create student profile
        cv_text, profile_content = self.analyze_cv(cv_path, career_goals)
        if not cv_text:
            return False

        # Create profile for matching (simplified)
        student_profile = {
            'summary': cv_text[:500],
            'cv_text': cv_text,  # Full CV text for keyword analysis
            'skills': ['Python', 'Java', 'SQL', 'Machine Learning', 'React', 'Node.js'],
            'desired_role': 'Software Engineer',
            'industry': 'fintech',
            'field_of_study': 'Computer Science',
            'location': 'South Africa'
        }

        # Discover jobs
        jobs_found = self.discover_jobs(student_profile)

        # Match jobs
        if jobs_found > 0:
            matched_jobs = self.match_jobs(student_profile)

        # Summary
        elapsed = datetime.now() - self.start_time
        if not self.quiet:
            print(f"\n⏱️  Analysis completed in {elapsed.total_seconds():.1f} seconds")
            print("="*70)

        return True


# Complete student career platform
class CareerBoostPlatform:
    """
    Complete student career platform with coordinated AI agents
    """
    def __init__(self):
        # Initialize coordinated agents
        self.agents = {
            'profile_builder': profile_builder,
            'job_matcher': job_matcher,
            'ats_optimizer': ats_optimizer,
            'cv_rewriter': cv_rewriter,
            'cover_letter_agent': cover_letter_agent,
            'interview_prep_agent': interview_prep_agent
        }
        self.students = {}
        self.jobs = {}
        self.applications = {}
        self.sa_customizations = sa_customizations
        self.ethical_guidelines = ethical_guidelines
        self.daily_application_counts = {}  # Track applications per student per day

    def onboard_student(self, student_cv, career_goals, consent_given=False):
        """
        Step 1: Create student profile using Profile Builder agent with ethical consent
        """
        print("👤 Onboarding new student...")

        # Ethical requirement: Must obtain consent for data processing
        if not consent_given:
            print("\n⚠️  ETHICAL CONSENT REQUIRED")
            print("This platform uses AI to assist with career development.")
            print("We require your explicit consent to:")
            print("• Process and analyze your CV")
            print("• Use AI for personalized recommendations")
            print("• Store data securely for 2 years (POPIA/GDPR compliant)")
            print("\nDo you consent to these terms? (Type 'yes' to continue)")
            consent_response = input().strip().lower()
            if consent_response not in ['yes', 'y', 'consent']:
                print("❌ Consent not given. Cannot proceed with onboarding.")
                return None, None

        profile = profile_builder.run(f"""
        Analyze CV: {student_cv}
        Career Goals: {career_goals}

        Create comprehensive profile including:
        - Education background
        - Work experience
        - Skills assessment
        - Career aspirations
        - Areas for development
        """)

        student_id = generate_student_id()

        # Obtain ethical consent for data processing
        consent_id = self.ethical_guidelines.manage_data_consent(
            student_id=student_id,
            data_types=['cv_content', 'career_goals', 'application_history', 'performance_data'],
            purpose='AI-powered career assistance and job matching',
            retention_period='2 years'
        )

        self.students[student_id] = {
            'profile': profile.content if hasattr(profile, 'content') else str(profile),
            'cv_text': student_cv,
            'career_goals': career_goals,
            'onboarded_at': datetime.now(),
            'consent_id': consent_id,
            'cv_engine': None,  # Will be created when needed
            'ethical_disclosure': self.ethical_guidelines.generate_ethical_disclosure('general', student_id)
        }

        print("✅ Student onboarded successfully!")
        print(f"📋 Student ID: {student_id}")
        print(f"🔒 Consent ID: {consent_id}")
        print("\n🛡️  Ethical Guidelines Applied:")
        print("• AI assistance will be transparent and helpful")
        print("• Your data is encrypted and POPIA/GDPR compliant")
        print("• You can withdraw consent at any time")

        return student_id, self.students[student_id]

    def find_matching_jobs(self, student_id, location="South Africa", num_jobs=10):
        """
        Step 2: Discover and match jobs using Job Matcher agent
        """
        if student_id not in self.students:
            raise ValueError(f"Student {student_id} not found")

        student = self.students[student_id]
        print(f"🔍 Finding matching jobs for {student_id}...")

        # Create student profile for job matching
        student_profile = {
            'summary': student['cv_text'][:500],
            'cv_text': student['cv_text'],
            'skills': ['Python', 'JavaScript', 'React', 'Node.js'],  # Would be extracted from profile
            'desired_role': 'Software Engineer',  # Would be extracted from profile
            'industry': 'Technology',
            'location': location
        }

        # Discover new jobs
        matched_jobs = discover_new_jobs(student_profile, location, verbose=True)

        # Filter and rank top matches with SA customizations
        top_matches = []
        for job in matched_jobs[:num_jobs * 2]:  # Get more jobs to allow for SA filtering
            base_score = job.get('match_score', 0)

            # Apply SA customizations to enhance job matching
            enhanced_job = self.sa_customizations.enhance_job_matching(job, student_profile)

            # Calculate SA-adjusted score
            sa_adjustments = enhanced_job.get('sa_score_adjustments', [])
            total_adjustment = sum(adj.get('adjustment', 0) for adj in sa_adjustments)
            adjusted_score = min(100, base_score + total_adjustment)  # Cap at 100

            # Prioritize first job opportunities for graduates
            if student_profile.get('is_recent_graduate', True):
                job_title = job.get('title', '').lower()
                if any(keyword in job_title for keyword in ['learnership', 'internship', 'graduate', 'junior', 'entry']):
                    adjusted_score += 10  # Bonus for first job opportunities

            # Apply minimum threshold with SA considerations
            min_score = 40 if student_profile.get('is_recent_graduate', True) else 50

            if adjusted_score >= min_score:
                job_id = f"{job.get('company', 'Unknown')}_{hash(job.get('url', ''))}"

                # Store enhanced job data
                self.jobs[job_id] = enhanced_job

                match_data = {
                    'job_id': job_id,
                    'job': enhanced_job,
                    'base_match_score': base_score,
                    'adjusted_match_score': adjusted_score,
                    'sa_adjustments': sa_adjustments,
                    'sa_recommendations': self._get_sa_job_recommendations(enhanced_job, student_profile)
                }

                top_matches.append(match_data)

        # Sort by adjusted score and return top matches
        top_matches.sort(key=lambda x: x['adjusted_match_score'], reverse=True)
        top_matches = top_matches[:num_jobs]

        print(f"✅ Found {len(top_matches)} SA-tailored job matches!")
        return top_matches

    def _get_sa_job_recommendations(self, job: Dict, student_profile: Dict) -> List[str]:
        """Generate SA-specific job recommendations"""
        recommendations = []

        # Transport considerations
        transport_info = job.get('transport_considerations', {})
        if transport_info.get('commute_cost'):
            recommendations.append(f"💰 Transport cost estimate: {transport_info['commute_cost']}/month")

        # Remote work
        if job.get('remote_work') or job.get('hybrid_work'):
            recommendations.append("🏠 Remote/hybrid opportunity - saves on transport costs")

        # First job opportunities
        job_title = job.get('title', '').lower()
        if any(keyword in job_title for keyword in ['learnership', 'internship', 'graduate']):
            recommendations.append("🎓 Great first job opportunity - prioritizes experience over extensive requirements")

        # Salary realism
        salary_info = job.get('salary_realism', {})
        if salary_info.get('adjusted_range'):
            recommendations.append(f"💵 Realistic salary range: {salary_info['adjusted_range']}")

        # Skills development
        if 'learnership' in job_title:
            recommendations.append("📚 Learnership provides paid training and NQF qualification")

        # Transport allowance
        benefits = job.get('benefits', [])
        if benefits and any('transport' in benefit.lower() for benefit in benefits):
            recommendations.append("🚌 Transport allowance included in benefits")

        return recommendations[:3]  # Limit to top 3 recommendations

    def apply_to_job(self, student_id, job_id):
        """
        Step 3: Generate tailored application materials using CV and Cover Letter agents
        """
        if student_id not in self.students:
            raise ValueError(f"Student {student_id} not found")
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        student = self.students[student_id]
        job = self.jobs[job_id]

        print(f"📝 Preparing application for {job['title']} at {job['company']}...")

        # Create CV tailoring engine if not exists
        if student['cv_engine'] is None:
            student_profile = {
                'name': student_id,
                'skills': ['Python', 'JavaScript', 'React', 'Node.js'],
                'experience': 'Entry-level developer'
            }
            student['cv_engine'] = CVTailoringEngine(student['cv_text'], student_profile)

        cv_engine = student['cv_engine']

        # Generate tailored CV with ethical validation
        print("📄 Generating tailored CV...")
        tailored_cv, ats_analysis = cv_engine.generate_tailored_cv(job)

        # Ethical validation: Check CV optimization doesn't fabricate experience
        original_cv = student['cv_text']
        ethical_validation = self.ethical_guidelines.validate_cv_optimization(
            original_cv=original_cv,
            optimized_cv=tailored_cv,
            student_consent=True  # Assumed from onboarding
        )

        if not ethical_validation['ethical_compliant']:
            print("⚠️  ETHICAL CONCERN DETECTED")
            for warning in ethical_validation['warnings']:
                print(f"   • {warning}")
            print("\nRecommendations:")
            for rec in ethical_validation['recommendations']:
                print(f"   • {rec}")

            proceed = input("\nProceed with application? (yes/no): ").strip().lower()
            if proceed not in ['yes', 'y']:
                print("❌ Application cancelled for ethical reasons.")
                return None, None

        # Generate cover letter
        print("📧 Generating cover letter...")
        cover_letter = cv_engine.generate_cover_letter(job, tailored_cv)

        # Check daily application limits (ethical guideline: quality over quantity)
        today = datetime.now().strftime('%Y-%m-%d')
        student_daily_key = f"{student_id}_{today}"

        daily_count = self.daily_application_counts.get(student_daily_key, 0)

        # Ethical validation: Application submission limits
        match_score = job.get('adjusted_match_score', job.get('match_score', 0))
        application_validation = self.ethical_guidelines.validate_application_submission(
            job_match_score=match_score,
            application_count_today=daily_count,
            customization_level='high'  # Assume high customization with AI tailoring
        )

        if not application_validation['can_submit']:
            print("⚠️  ETHICAL APPLICATION LIMITS")
            for warning in application_validation['warnings']:
                print(f"   • {warning}")
            print("\nRecommendations:")
            for rec in application_validation['recommendations']:
                print(f"   • {rec}")

            proceed = input("\nProceed with application? (yes/no): ").strip().lower()
            if proceed not in ['yes', 'y']:
                print("❌ Application cancelled to maintain ethical standards.")
                return None, None

        # Package application
        application_package = {
            'student_id': student_id,
            'job_id': job_id,
            'cv': tailored_cv,
            'cover_letter': cover_letter,
            'ats_analysis': ats_analysis,
            'match_score': job.get('match_score', 0),
            'adjusted_match_score': job.get('adjusted_match_score', job.get('match_score', 0)),
            'job_url': job.get('url', ''),
            'company': job.get('company', ''),
            'job_title': job.get('title', ''),
            'applied_at': datetime.now(),
            'ethical_validation': {
                'cv_compliant': ethical_validation['ethical_compliant'],
                'application_compliant': application_validation['can_submit'],
                'quality_assessment': application_validation['quality_assessment']
            },
            'disclosure_statement': self.ethical_guidelines.generate_ethical_disclosure('cv_optimization', student_id)
        }

        # Track application and update daily count
        application_id = f"{student_id}_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        self.applications[application_id] = application_package
        self.daily_application_counts[student_daily_key] = daily_count + 1

        print("✅ Application package ready!")
        print(f"   📄 CV: {len(tailored_cv) if tailored_cv else 0} characters")
        print(f"   📧 Cover Letter: {len(cover_letter) if cover_letter else 0} characters")
        print(f"   🛡️  Ethical Score: {application_validation['quality_assessment']}")

        return application_id, application_package

    def prepare_for_interview(self, student_id, job_id):
        """
        Step 4: Interview preparation using Interview agents
        """
        if student_id not in self.students:
            raise ValueError(f"Student {student_id} not found")
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        student = self.students[student_id]
        job = self.jobs[job_id]

        print(f"🎯 Preparing for interview: {job['title']} at {job['company']}")

        # Create interview simulator
        simulator = MockInterviewSimulator(job['title'], job['company'], student)

        # Generate interview questions
        print("❓ Generating interview questions...")
        questions = simulator.questions  # Uses existing question generation

        # Provide option for copilot-assisted practice
        print("🤖 Starting mock interview (with optional copilot hints)...")
        print("Note: Copilot hints are for learning purposes only")

        # For demo purposes, return the setup
        interview_prep = {
            'questions': questions[:5],  # First 5 questions
            'simulator': simulator,
            'job': job,
            'tips': [
                "Practice using the STAR method (Situation-Task-Action-Result)",
                "Prepare specific examples from your experience",
                "Research the company and role thoroughly",
                "Practice answering questions out loud"
            ]
        }

        print("✅ Interview preparation complete!")
        return interview_prep

    def track_application(self, application_id):
        """
        Track application status and follow-ups
        """
        if application_id not in self.applications:
            raise ValueError(f"Application {application_id} not found")

        application = self.applications[application_id]

        # Calculate follow-up date (1 week after application)
        followup_date = application['applied_at'] + timedelta(days=7)

        tracking_info = {
            'application_id': application_id,
            'status': 'Applied',
            'applied_date': application['applied_at'],
            'follow_up_date': followup_date,
            'days_since_applied': (datetime.now() - application['applied_at']).days,
            'job_details': {
                'company': application['company'],
                'title': application['job_title'],
                'url': application['job_url']
            },
            'next_action': "Follow up in {} days".format(max(0, (followup_date - datetime.now()).days))
        }

        return tracking_info

    def get_student_dashboard(self, student_id):
        """
        Get comprehensive student dashboard
        """
        if student_id not in self.students:
            raise ValueError(f"Student {student_id} not found")

        student = self.students[student_id]

        # Get student's applications
        student_applications = [
            self.track_application(app_id)
            for app_id, app in self.applications.items()
            if app['student_id'] == student_id
        ]

        dashboard = {
            'student_id': student_id,
            'profile': student['profile'],
            'onboarded_at': student['onboarded_at'],
            'total_applications': len(student_applications),
            'applications': student_applications,
            'recent_activity': sorted(
                [app['applied_date'] for app in student_applications],
                reverse=True
            )[:5] if student_applications else []
        }

        return dashboard

    def search_knowledge_base(self, query: str, sources: List[str] = None, n_results: int = 3):
        """
        Search the knowledge base for relevant context

        Args:
            query: Search query
            sources: List of knowledge sources to search
            n_results: Number of results per source
        """
        try:
            context = knowledge_base.retrieve_context(query, sources, n_results)

            # Format results for easy consumption
            formatted_results = {}
            for source, results in context.items():
                formatted_results[source] = []
                for i, doc in enumerate(results['documents']):
                    formatted_results[source].append({
                        'text': doc,
                        'metadata': results['metadatas'][i],
                        'similarity_score': 1 - results['distances'][i],  # Convert distance to similarity
                        'id': results['ids'][i]
                    })

            return formatted_results

        except Exception as e:
            print(f"❌ Error searching knowledge base: {e}")
            return {}

    def get_market_insights(self, student_id: str):
        """
        Get comprehensive SA market insights tailored to a student's profile
        """
        if student_id not in self.students:
            raise ValueError(f"Student {student_id} not found")

        student = self.students[student_id]

        # Extract student profile information for SA customizations
        student_profile = {
            'education_level': self._extract_education_level(student['profile']),
            'preferred_regions': ['gauteng', 'western_cape'],  # Default SA regions
            'is_recent_graduate': True,  # Assume recent graduate for SA context
            'career_goals': student.get('career_goals', 'software engineer')
        }

        # Get comprehensive SA insights using customizations
        sa_insights = self.sa_customizations.get_market_insights(student_profile)

        # Enhance with knowledge base search for additional context
        kb_insights = {
            'industry_specific': self.search_knowledge_base(
                f"{student_profile['career_goals']} jobs in South Africa",
                sources=['job_descriptions', 'sa_context'],
                n_results=2
            ),
            'skills_requirements': self.search_knowledge_base(
                f"skills needed for {student_profile['career_goals']} roles",
                sources=['skills_taxonomy', 'job_descriptions'],
                n_results=3
            )
        }

        # Combine SA customizations with knowledge base insights
        comprehensive_insights = {
            **sa_insights,  # SA-specific customizations
            'knowledge_base_insights': kb_insights,
            'student_profile': student_profile,
            'generated_at': datetime.now().isoformat()
        }

        return comprehensive_insights

    def _extract_education_level(self, profile_text: str) -> str:
        """Extract education level from profile text for SA customizations"""
        profile_lower = profile_text.lower()

        if any(term in profile_lower for term in ['bachelor', 'degree', 'bsc', 'ba', 'bcom', 'llb']):
            return 'degree'
        elif any(term in profile_lower for term in ['diploma', 'national diploma']):
            return 'diploma'
        elif any(term in profile_lower for term in ['certificate', 'nqf']):
            return 'certificate'
        elif any(term in profile_lower for term in ['matric', 'grade 12']):
            return 'matric'
        elif any(term in profile_lower for term in ['tvet', 'technical vocational']):
            return 'tvet'

        return 'degree'  # Default assumption

    def enhance_with_knowledge(self, agent_response, query_context):
        """
        Enhance agent responses with knowledge base context
        """
        try:
            # Search for relevant context
            context = self.search_knowledge_base(query_context, n_results=2)

            # Combine agent response with knowledge base insights
            enhanced_response = {
                'agent_response': agent_response,
                'knowledge_context': context,
                'enhancement_type': 'retrieval_augmented'
            }

            return enhanced_response

        except Exception as e:
            print(f"⚠️ Could not enhance with knowledge: {e}")
            return agent_response

    def get_knowledge_stats(self):
        """
        Get comprehensive knowledge base statistics
        """
        try:
            stats = knowledge_base.get_all_stats()

            # Calculate totals
            total_docs = sum(s['document_count'] if s else 0 for s in stats.values())
            sources_count = len([s for s in stats.values() if s])

            return {
                'total_documents': total_docs,
                'active_sources': sources_count,
                'sources': stats,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ Error getting knowledge stats: {e}")
            return {'error': str(e)}


def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Job Market AI Analyzer - Advanced job matching for students",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Run with default CV and settings
  python main.py --cv-path my_cv.pdf       # Use specific CV file
  python main.py --verbose                 # Show detailed progress
  python main.py --quiet                   # Minimal output
  python main.py --goals "Data Scientist"  # Custom career goals
        """
    )

    parser.add_argument(
        '--cv-path',
        type=str,
        default=None,
        help='Path to CV PDF file (overrides CV_FILE_PATH env var)'
    )

    parser.add_argument(
        '--goals',
        type=str,
        default=None,
        help='Career goals (overrides CAREER_GOALS env var)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed progress information'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimal output mode'
    )

    # CareerBoost Platform options
    parser.add_argument(
        '--platform', '-p',
        action='store_true',
        help='Use CareerBoost Platform mode'
    )

    parser.add_argument(
        '--onboard',
        type=str,
        help='Onboard student with CV file path'
    )

    parser.add_argument(
        '--student-id',
        type=str,
        help='Student ID for platform operations'
    )

    parser.add_argument(
        '--find-jobs',
        action='store_true',
        help='Find matching jobs for student'
    )

    parser.add_argument(
        '--apply',
        type=str,
        help='Apply to job (provide job ID)'
    )

    parser.add_argument(
        '--interview-prep',
        type=str,
        help='Prepare for interview (provide job ID)'
    )

    parser.add_argument(
        '--dashboard',
        action='store_true',
        help='Show student dashboard'
    )

    # Knowledge Base options
    parser.add_argument(
        '--knowledge-search',
        type=str,
        help='Search the knowledge base (provide query)'
    )

    parser.add_argument(
        '--market-insights',
        action='store_true',
        help='Get market insights for student'
    )

    parser.add_argument(
        '--sa-insights',
        action='store_true',
        help='Get South Africa-specific career insights'
    )

    parser.add_argument(
        '--knowledge-stats',
        action='store_true',
        help='Show knowledge base statistics'
    )

    # Ethical compliance options
    parser.add_argument(
        '--ethical-audit',
        action='store_true',
        help='Generate ethical compliance audit report'
    )

    parser.add_argument(
        '--withdraw-consent',
        type=str,
        help='Withdraw data consent (provide consent ID)'
    )

    parser.add_argument(
        '--consent-status',
        action='store_true',
        help='Check consent status'
    )

    return parser


def main():
    """Main entry point with professional CLI"""
    parser = create_parser()
    args = parser.parse_args()

    # Check if using CareerBoost Platform
    if args.platform:
        run_careerboost_platform(args)
        return

    # Original JobMarketAnalyzer mode
    # Initialize analyzer
    analyzer = JobMarketAnalyzer(verbose=args.verbose, quiet=args.quiet)

    # Display banner
    analyzer.print_banner()

    # Get configuration
    cv_path = args.cv_path or os.getenv('CV_FILE_PATH')
    if not cv_path:
        if os.path.exists('CV.pdf'):
            cv_path = 'CV.pdf'
        else:
            analyzer.print_error("No CV file specified. Use --cv-path or set CV_FILE_PATH environment variable")
            sys.exit(1)

    career_goals = args.goals or os.getenv('CAREER_GOALS', CAREER_GOALS_DEFAULT)

    # Validate CV exists
    if not os.path.exists(cv_path):
        analyzer.print_error(f"CV file not found: {cv_path}")
        sys.exit(1)

    # Run analysis
    success = analyzer.run_analysis(cv_path, career_goals)

    if not success:
        sys.exit(1)


def run_careerboost_platform(args):
    """Run the CareerBoost platform with coordinated AI agents"""
    print("="*80)
    print("🚀 CAREERBOOST AI PLATFORM")
    print("="*80)
    print("Complete career acceleration system with coordinated AI agents")
    print("="*80)

    # Initialize platform
    platform = CareerBoostPlatform()

    # Handle different platform operations
    if args.onboard:
        # Onboard new student
        cv_path = args.onboard
        if not os.path.exists(cv_path):
            print(f"❌ CV file not found: {cv_path}")
            sys.exit(1)

        # Read CV
        cv_text = ""
        with fitz.open(cv_path) as doc:
            for page in doc:
                cv_text += page.get_text()

        career_goals = args.goals or CAREER_GOALS_DEFAULT

        student_id, profile = platform.onboard_student(cv_text, career_goals, consent_given=True)  # CLI assumes consent
        if student_id:
            print(f"\n👤 Student ID: {student_id}")
            print(f"📊 Profile created successfully!")
        else:
            print("❌ Onboarding cancelled.")
            return

    elif args.student_id:
        student_id = args.student_id

        if args.find_jobs:
            # Find matching jobs
            try:
                matches = platform.find_matching_jobs(student_id)
                print(f"\n🏆 TOP JOB MATCHES for {student_id}:")
                for i, match in enumerate(matches[:5], 1):
                    job = match['job']
                    print(f"{i}. {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                    print(f"   Match Score: {match['match_score']:.1f}%")
                    print(f"   Job ID: {match['job_id']}")
                    print()
            except ValueError as e:
                print(f"❌ Error: {e}")

        elif args.apply:
            # Apply to job
            job_id = args.apply
            try:
                application_id, application = platform.apply_to_job(student_id, job_id)
                print(f"\n✅ Application submitted!")
                print(f"📋 Application ID: {application_id}")
                print(f"🏢 Company: {application['company']}")
                print(f"💼 Position: {application['job_title']}")
            except ValueError as e:
                print(f"❌ Error: {e}")

        elif args.interview_prep:
            # Interview preparation
            job_id = args.interview_prep
            try:
                prep = platform.prepare_for_interview(student_id, job_id)
                print(f"\n🎯 INTERVIEW PREPARATION READY")
                print(f"❓ Questions prepared: {len(prep['questions'])}")
                print(f"🤖 Simulator: Ready")
                print(f"💡 Practice Tips:")
                for tip in prep['tips']:
                    print(f"   • {tip}")
            except ValueError as e:
                print(f"❌ Error: {e}")

        elif args.dashboard:
            # Show dashboard
            try:
                dashboard = platform.get_student_dashboard(student_id)
                print(f"\n📊 STUDENT DASHBOARD - {student_id}")
                print(f"📅 Onboarded: {dashboard['onboarded_at'].strftime('%Y-%m-%d')}")
                print(f"📝 Total Applications: {dashboard['total_applications']}")

                if dashboard['applications']:
                    print(f"\n📋 Recent Applications:")
                    for app in dashboard['applications'][:3]:
                        print(f"   • {app['job_details']['title']} at {app['job_details']['company']}")
                        print(f"     Applied: {app['applied_date'].strftime('%Y-%m-%d')}")
                        print(f"     Status: {app['status']} | Next: {app['next_action']}")
                        print()
            except ValueError as e:
                print(f"❌ Error: {e}")

        elif args.knowledge_search:
            # Search knowledge base
            query = args.knowledge_search
            print(f"🔍 Searching knowledge base for: '{query}'")

            results = platform.search_knowledge_base(query)
            if results:
                for source, docs in results.items():
                    if docs:
                        print(f"\n📚 {source.upper()}:")
                        for i, doc in enumerate(docs[:2], 1):  # Show top 2 per source
                            print(f"   {i}. {doc['text'][:100]}...")
                            print(f"     Similarity: {doc['similarity_score']:.2f}")
                            print()
            else:
                print("❌ No results found")

        elif args.market_insights or args.sa_insights:
            # Get comprehensive market insights
            try:
                insights = platform.get_market_insights(student_id)
                print(f"\n🇿🇦 SOUTH AFRICA CAREER INSIGHTS for {student_id}")
                print("=" * 60)

                # Show SA-specific insights
                print("📊 YOUTH EMPLOYMENT REALITY:")
                for challenge in insights.get('key_challenges', []):
                    print(f"   • {challenge}")

                print(f"\n💡 SUCCESS FACTORS:")
                for factor in insights.get('success_factors', []):
                    print(f"   • {factor}")

                # Transport considerations
                transport = insights.get('transport_reality', {})
                if transport.get('general_advice'):
                    print(f"\n🚌 TRANSPORT REALITY:")
                    print(f"   {transport['general_advice']}")
                    for rec in transport.get('recommendations', [])[:2]:
                        print(f"   • {rec}")

                # Salary expectations
                salary = insights.get('salary_expectations', {})
                if salary.get('realistic_expectations'):
                    print(f"\n💰 SALARY REALISM:")
                    for expectation in salary['realistic_expectations'][:3]:
                        print(f"   • {expectation}")

                # Skills development
                skills_dev = insights.get('skills_development', {})
                if skills_dev.get('eligible_programs'):
                    print(f"\n🎓 SKILLS DEVELOPMENT PATHWAYS:")
                    for program in skills_dev['eligible_programs']:
                        salary_range = skills_dev.get('salary_expectations', {}).get(program, 'Contact provider')
                        print(f"   • {program.title()}: {salary_range}")

                # First job strategy
                first_job = insights.get('first_job_strategy', {})
                if first_job.get('recommended_pathways'):
                    print(f"\n🚀 FIRST JOB STRATEGY:")
                    print(f"   Timeline: {first_job.get('timeline', 'Varies')}")
                    print(f"   Pathways: {', '.join(first_job['recommended_pathways'])}")
                    for action in first_job.get('action_plan', [])[:2]:
                        print(f"   • {action}")

                # Language considerations
                languages = insights.get('language_considerations', {})
                if languages.get('additional_languages'):
                    print(f"\n🗣️ WORKPLACE LANGUAGES:")
                    print(f"   Primary: {languages.get('primary_language', 'English')}")
                    print(f"   Additional: {', '.join(languages['additional_languages'][:3])}")

            except ValueError as e:
                print(f"❌ Error: {e}")

        elif args.knowledge_stats:
            # Show knowledge base statistics
            stats = platform.get_knowledge_stats()
            print(f"\n🧠 KNOWLEDGE BASE STATISTICS")
            print("=" * 50)
            print(f"📊 Total Documents: {stats.get('total_documents', 0)}")
            print(f"📚 Active Sources: {stats.get('active_sources', 0)}")
            print(f"🕒 Last Updated: {stats.get('last_updated', 'Unknown')}")

            if 'sources' in stats:
                print(f"\n📋 SOURCES:")
                for source_name, source_stats in stats['sources'].items():
                    if source_stats:
                        print(f"   • {source_name}: {source_stats['document_count']} documents")
                        print(f"     {source_stats['description']}")
                    else:
                        print(f"   • {source_name}: Not initialized")
            print()

        elif args.ethical_audit:
            # Generate ethical audit report
            audit_report = platform.ethical_guidelines.get_ethical_audit_report()
            print(f"\n🛡️  ETHICAL COMPLIANCE AUDIT REPORT")
            print("=" * 50)
            print(f"📊 Compliance Rate: {audit_report.get('compliance_rate', 0):.1f}%")
            print(f"⚠️  Warnings: {audit_report.get('warnings_count', 0)}")
            print(f"🚨 Critical Issues: {audit_report.get('critical_issues', 0)}")
            print(f"📝 Total Audits: {audit_report.get('total_checks', 0)}")

            if audit_report.get('recommendations'):
                print(f"\n💡 RECOMMENDATIONS:")
                for rec in audit_report['recommendations']:
                    print(f"   • {rec}")

            if audit_report.get('category_breakdown'):
                print(f"\n📋 CATEGORY BREAKDOWN:")
                for category, count in audit_report['category_breakdown'].items():
                    print(f"   • {category}: {count} checks")
            print()

        elif args.withdraw_consent:
            # Withdraw data consent
            consent_id = args.withdraw_consent
            success = platform.ethical_guidelines.withdraw_consent(consent_id)

            if success:
                print(f"✅ Consent withdrawn successfully for ID: {consent_id}")
                print("📝 Your data will be securely deleted within 30 days")
                print("🔒 You can re-consent at any time for continued service")
            else:
                print(f"❌ Consent ID not found: {consent_id}")
                print("💡 Check your consent ID from the onboarding process")

        elif args.consent_status:
            # Check consent status
            active_consents = len([c for c in platform.ethical_guidelines.consent_records.values()
                                 if not c.get('consent_withdrawn', False)])
            total_consents = len(platform.ethical_guidelines.consent_records)

            print(f"\n🔒 CONSENT MANAGEMENT STATUS")
            print("=" * 50)
            print(f"📋 Active Consents: {active_consents}")
            print(f"📊 Total Consents: {total_consents}")
            print(f"🔄 Withdrawn: {total_consents - active_consents}")

            print(f"\n🛡️  DATA PROTECTION:")
            print("• End-to-end encryption (AES-256)")
            print("• POPIA (South Africa) and GDPR compliant")
            print("• Secure storage in South Africa")
            print("• Right to withdraw consent anytime")
            print()

        else:
            print("❌ No operation specified. Use --help for available options.")
            print("\nAvailable operations:")
            print("  --onboard <cv_file>     : Onboard new student")
            print("  --find-jobs             : Find matching jobs")
            print("  --apply <job_id>        : Apply to specific job")
            print("  --interview-prep <job_id>: Prepare for interview")
            print("  --dashboard             : Show student dashboard")
            print("  --knowledge-search <query>: Search knowledge base")
            print("  --market-insights       : Get market insights")
            print("  --sa-insights           : Get SA-specific career insights")
            print("  --knowledge-stats       : Show knowledge base stats")
            print("  --ethical-audit         : Generate ethical compliance report")
            print("  --withdraw-consent <id> : Withdraw data consent")
            print("  --consent-status        : Check consent status")

    else:
        print("🎯 CareerBoost Platform Ready!")
        print("\n📚 Getting Started:")
        print("1. Onboard a student: python main.py --platform --onboard CV.pdf")
        print("2. Find jobs: python main.py --platform --student-id <ID> --find-jobs")
        print("3. Apply: python main.py --platform --student-id <ID> --apply <job_id>")
        print("4. Interview prep: python main.py --platform --student-id <ID> --interview-prep <job_id>")
        print("5. Dashboard: python main.py --platform --student-id <ID> --dashboard")
        print("6. Search knowledge: python main.py --platform --knowledge-search 'Python developer salary'")
        print("7. Market insights: python main.py --platform --student-id <ID> --market-insights")
        print("8. SA career insights: python main.py --platform --student-id <ID> --sa-insights")
        print("9. Knowledge stats: python main.py --platform --knowledge-stats")

        print(f"\n🤖 AI Agents Ready: {len(platform.agents)} specialized agents")
        for i, (name, agent) in enumerate(platform.agents.items(), 1):
            print(f"   {i}. {agent.name}")


if __name__ == "__main__":
    main()