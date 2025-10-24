from agno.agent import Agent
from agno.tools.file import FileTools
from agno.models.google import Gemini
import fitz  # PyMuPDF
import chromadb
import numpy as np
import google.genai as genai
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import json
import os
import sys
import argparse
from dotenv import load_dotenv

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

# Initialize Gemini client for embeddings (suppress verbose logging)
import logging
logging.getLogger('google.genai').setLevel(logging.WARNING)
logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('agno').setLevel(logging.WARNING)

# Suppress API key confirmation messages by temporarily unsetting conflicting env vars
import os

# Temporarily unset GEMINI_API_KEY to prevent the "Both keys set" message
gemini_key_backup = os.environ.get('GEMINI_API_KEY')
if 'GEMINI_API_KEY' in os.environ:
    del os.environ['GEMINI_API_KEY']

client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

# Restore GEMINI_API_KEY if it was set
if gemini_key_backup:
    os.environ['GEMINI_API_KEY'] = gemini_key_backup

# Vector Database for job postings
chroma_client = chromadb.Client()

# Check if collection exists, create or get it
try:
    jobs_collection = chroma_client.get_collection(name="job_postings")
except:
    jobs_collection = chroma_client.create_collection(
        name="job_postings",
        metadata={"hnsw:space": "cosine"}
    )

# Profile Builder Agent
# Temporarily unset GEMINI_API_KEY to prevent the "Both keys set" message
gemini_key_backup = os.environ.get('GEMINI_API_KEY')
if 'GEMINI_API_KEY' in os.environ:
    del os.environ['GEMINI_API_KEY']

profile_builder = Agent(
    name="Profile Analyst",
    model=Gemini(id="gemini-2.0-flash"),
    tools=[FileTools()],
    instructions="""Analyze student CVs and profiles to extract:
    EDUCATION:
    - Degree/diploma and field of study
    - GPA and academic achievements
    - Relevant coursework and projects

    EXPERIENCE:
    - Work history (internships, part-time jobs, volunteer work)
    - Quantifiable achievements (increased X by Y%)
    - Responsibilities and impact

    SKILLS:
    - Technical skills (programming languages, software tools)
    - Soft skills (communication, teamwork, problem-solving)
    - Certifications and training

    CAREER ASPIRATIONS:
    - Short-term goals (next 1-2 years)
    - Long-term vision (5+ years)
    - Preferred industries and company types
    - Geographic preferences

    Create a structured profile with:
    - Skill proficiency levels (beginner, intermediate, advanced)
    - Experience gaps that need addressing
    - Competitive advantages and unique selling points
    """,
    markdown=True
)

# Restore GEMINI_API_KEY if it was set
if gemini_key_backup:
    os.environ['GEMINI_API_KEY'] = gemini_key_backup

# Job Matcher Agent
# Temporarily unset GEMINI_API_KEY to prevent the "Both keys set" message
gemini_key_backup = os.environ.get('GEMINI_API_KEY')
if 'GEMINI_API_KEY' in os.environ:
    del os.environ['GEMINI_API_KEY']

job_matcher = Agent(
    name="Job Matching Specialist",
    model=Gemini(id="gemini-2.0-flash"),
    tools=[FileTools()],
    instructions="""Match students with job opportunities using multi-dimensional analysis:

    SCORING METHODOLOGY:
    1. Aspiration Fit (0-100): Analyze job description, company info, growth potential
       - Does role align with student's 5-year goals?
       - Is industry/company type preferred?
       - Career advancement opportunities?

    2. Skill Fit (0-100): Compare required vs. offered skills
       - Hard match: Exact skill matches (Python, SQL)
       - Soft match: Transferable skills (research → analysis)
       - Semantic similarity: "machine learning" ≈ "ML" ≈ "AI"

    3. Experience Fit (0-100): Evaluate seniority and background
       - Years of experience required vs. student has
       - Educational requirements (degree, certifications)
       - Industry-specific experience

    4. Practical Fit (0-100): Location, work arrangement, company culture
       - Commute distance and transport availability
       - Remote/hybrid options
       - Company values match student preferences

    WEIGHTED OVERALL SCORE:
    Overall = (Aspiration × 0.40) + (Skills × 0.35) + (Experience × 0.15) + (Practical × 0.10)

    RECOMMENDATION THRESHOLD:
    - 70+: Highly recommended (show to student)
    - 50-69: Moderate fit (show with caveats)
    - <50: Not recommended (filter out)

    For each recommended job, provide:
    - Overall match score (0-100)
    - Breakdown of subscores
    - Reasoning for recommendation
    - Action items (skills to highlight, gaps to address)""",
    markdown=True
)

# Restore GEMINI_API_KEY if it was set
if gemini_key_backup:
    os.environ['GEMINI_API_KEY'] = gemini_key_backup

# ATS Optimization Specialist
# Temporarily unset GEMINI_API_KEY to prevent the "Both keys set" message
gemini_key_backup = os.environ.get('GEMINI_API_KEY')
if 'GEMINI_API_KEY' in os.environ:
    del os.environ['GEMINI_API_KEY']

ats_optimizer = Agent(
    name="ATS Optimization Specialist",
    model=Gemini(id="gemini-2.0-flash"),
    instructions="""Optimize resumes for Applicant Tracking Systems (ATS):

    FORMATTING REQUIREMENTS:
    ✅ DO:
    - Use standard section headers ("Experience", "Education", "Skills")
    - Simple, clean fonts (Arial, Calibri, Times New Roman)
    - Standard bullet points (•, -, *)
    - Clear date formats (MM/YYYY)
    - Standard file format (PDF or .docx)

    ❌ AVOID:
    - Tables, text boxes, headers/footers (ATS can't parse)
    - Images, logos, graphics
    - Complex formatting (columns, unusual fonts)
    - Abbreviations without spelling out first mention
    - Creative section names ("My Journey" instead of "Experience")

    CONTENT OPTIMIZATION:
    1. Keyword Extraction: Identify exact keywords from job description
    2. Strategic Placement: Distribute keywords naturally across sections
    3. Avoid Keyword Stuffing: Maintain readability for humans
    4. Exact Matches: Use exact job title and skills mentioned
    5. Variations: Include synonyms and related terms
       Example: "Project Management" + "Project Manager" + "PM"

    ATS SCORING CRITERIA:
    - Keyword Match: 40%
    - Format Compliance: 25%
    - Section Completeness: 20%
    - Experience Relevance: 15%

    Provide ATS compatibility score (0-100) with specific improvements"""
)

# Restore GEMINI_API_KEY if it was set
if gemini_key_backup:
    os.environ['GEMINI_API_KEY'] = gemini_key_backup

# Semantic skill matching using Gemini embeddings
def semantic_skill_match(student_skills, required_skills):
    """
    Use word embeddings to handle synonyms and variations
    Example: "JavaScript" matches "JS", "ECMAScript"
    """
    if not student_skills or not required_skills:
        return [], 0
    
    try:
        # Generate embeddings for student skills
        student_embeddings = []
        for skill in student_skills:
            response = client.models.embed_content(
                model="text-embedding-004",
                contents=skill
            )
            student_embeddings.append(response.embeddings[0].values)

        # Generate embeddings for required skills
        required_embeddings = []
        for skill in required_skills:
            response = client.models.embed_content(
                model="text-embedding-004",
                contents=skill
            )
            required_embeddings.append(response.embeddings[0].values)
        
        # Convert to numpy arrays
        student_embeddings = np.array(student_embeddings)
        required_embeddings = np.array(required_embeddings)
        
        # Compute cosine similarity matrix
        # Normalize vectors for cosine similarity
        student_norm = student_embeddings / np.linalg.norm(student_embeddings, axis=1, keepdims=True)
        required_norm = required_embeddings / np.linalg.norm(required_embeddings, axis=1, keepdims=True)
        similarity_matrix = np.dot(student_norm, required_norm.T)
        
        # For each required skill, find best matching student skill
        matches = []
        for i, req_skill in enumerate(required_skills):
            best_match_idx = np.argmax(similarity_matrix[:, i])
            similarity_score = similarity_matrix[best_match_idx, i]
            
            if similarity_score > 0.75:  # High similarity threshold
                matches.append({
                    'required': req_skill,
                    'student_has': student_skills[best_match_idx],
                    'confidence': float(similarity_score)
                })
        
        match_percentage = len(matches) / len(required_skills) * 100
        return matches, match_percentage
    
    except Exception as e:
        print(f"Error in semantic skill matching: {e}")
        return [], 0


# Match student to jobs
def match_student_to_jobs(student_profile, jobs_collection):
    """
    Match a student profile to jobs in the ChromaDB collection
    """
    student_skills = student_profile.get('skills', [])
    
    try:
        # Create embedding for the student profile summary
        query_text = student_profile.get('summary', '')
        if not query_text:
            query_text = f"{student_profile.get('desired_role', '')} {student_profile.get('industry', '')}"

        query_response = client.models.embed_content(
            model="text-embedding-004",
            contents=query_text
        )
        query_embedding = query_response.embeddings[0].values

        # Query similar jobs from ChromaDB using manual embeddings
        results = jobs_collection.query(
            query_embeddings=[query_embedding],
            n_results=10
        )
        
        matched_jobs = []
        for i, job_id in enumerate(results['ids'][0]):
            job_metadata = results['metadatas'][0][i]
            # Convert skills string back to list
            skills_str = job_metadata.get('required_skills', '')
            required_skills = [s.strip() for s in skills_str.split(',')] if skills_str else []
            
            # Perform semantic skill matching
            skill_matches, match_score = semantic_skill_match(student_skills, required_skills)
            
            # Use the agent to perform detailed analysis
            analysis = job_matcher.run(f"""
            Analyze this job match:
            
            Student Profile: {student_profile}
            Job Description: {job_metadata.get('description', '')}
            Company: {job_metadata.get('company', '')}
            Required Skills: {required_skills}
            Skill Match Score: {match_score:.1f}%
            Skill Matches: {skill_matches}
            
            Provide a comprehensive match analysis with scores.
            """)
            
            matched_jobs.append({
                'job_id': job_id,
                'match_score': match_score,
                'analysis': analysis.content
            })
        
        return matched_jobs
    
    except Exception as e:
        print(f"Error matching jobs: {e}")
        return []

def discover_new_jobs(student_profile, location="Johannesburg", verbose=False):
    """
    Scrape job boards for new opportunities using advanced Playwright-based scraping
    """
    desired_role = student_profile.get('desired_role', 'software engineer')

    if verbose:
        print("🔄 Starting advanced job scraping with Playwright...")
        print(f"   🎯 Searching for: {desired_role} in {location}")

    # Use the advanced scraping from scrapper.py
    all_jobs = advanced_scrape_all(desired_role, location)

    if verbose:
        print(f"📊 Scraped {len(all_jobs)} total jobs")

    # Store in ChromaDB
    if all_jobs:
        store_jobs_in_db(all_jobs, jobs_collection)
        if verbose:
            print("💾 Jobs stored in database")
    elif verbose:
        print("⚠️ No jobs scraped, skipping database storage")

    # Match against student profile
    matched_jobs = match_student_to_jobs(student_profile, jobs_collection)

    return matched_jobs




def extract_skills_from_description(description):
    """
    Extract technical skills from job description using AI
    """
    # Common tech skills to look for
    common_skills = [
        'Python', 'Java', 'JavaScript', 'C++', 'C#', 'SQL', 'NoSQL',
        'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask',
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
        'Machine Learning', 'AI', 'Data Science', 'Data Analysis',
        'Git', 'Agile', 'Scrum', 'CI/CD'
    ]
    
    found_skills = []
    description_lower = description.lower()
    
    for skill in common_skills:
        if skill.lower() in description_lower:
            found_skills.append(skill)
    
    # Use Gemini for more sophisticated extraction
    try:
        extraction_agent = Agent(
            name="Skill Extractor",
            model=Gemini(id="gemini-2.0-flash"),
            instructions="Extract technical skills from job descriptions. Return as comma-separated list."
        )
        
        result = extraction_agent.run(f"Extract skills from: {description}")
        ai_skills = [s.strip() for s in result.content.split(',')]
        found_skills.extend(ai_skills)
        
        # Remove duplicates
        found_skills = list(set(found_skills))
    except:
        pass
    
    return found_skills


def store_jobs_in_db(jobs, collection):
    """
    Store scraped jobs in ChromaDB
    """
    for job in jobs:
        try:
            # Generate unique ID if not present
            job_id = job.get('id', f"{job['source']}_{hash(job['url'])}")

            # Extract skills from job description
            description = job.get('description', f"{job['title']} at {job['company']} in {job['location']}")
            required_skills = extract_skills_from_description(description)

            # Create embedding from available information
            embedding_text = f"{job['title']} {job['company']} {job['location']} {description} {' '.join(required_skills)}"

            response = client.models.embed_content(
                model="text-embedding-004",
                contents=embedding_text
            )
            embedding = response.embeddings[0].values

            # Add to ChromaDB
            collection.add(
                ids=[job_id],
                embeddings=[embedding],
                metadatas=[{
                    'title': job['title'],
                    'company': job['company'],
                    'location': job['location'],
                    'description': description,
                    'url': job['url'],
                    'source': job['source'],
                    'required_skills': ', '.join(required_skills),  # Convert list to string
                    'posted_date': datetime.now().isoformat()  # Use current date since scraper doesn't extract dates
                }],
                documents=[description]
            )
        except Exception as e:
            print(f"Error storing job {job.get('title', 'unknown')}: {e}")


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
            matched_jobs = match_student_to_jobs(student_profile, jobs_collection)

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

    def run_analysis(self, cv_path, career_goals=None):
        """Run complete analysis pipeline"""
        # Create student profile
        cv_text, profile_content = self.analyze_cv(cv_path, career_goals)
        if not cv_text:
            return False

        # Create profile for matching (simplified)
        student_profile = {
            'summary': cv_text[:500],
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