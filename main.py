import fitz  # PyMuPDF
import time
from datetime import datetime
import json
import os
import sys
import argparse
from dotenv import load_dotenv

# Import agents
from agents import profile_builder, job_matcher, ats_optimizer, cv_rewriter

# Import utilities
from utils import jobs_collection, store_jobs_in_db, discover_new_jobs, match_student_to_jobs, CVTailoringEngine, MockInterviewSimulator, interview_copilot

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

    return parser


def main():
    """Main entry point with professional CLI"""
    parser = create_parser()
    args = parser.parse_args()

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


if __name__ == "__main__":
    main()