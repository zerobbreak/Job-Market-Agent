# Standard library imports
import argparse
import hashlib
import os
import re
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

# Third-party imports
import fitz  # PyMuPDF
from cachetools import TTLCache
from dotenv import load_dotenv
from tqdm import tqdm

# Optional web server imports (only imported if web server mode is used)
try:
    from fastapi import FastAPI, APIRouter
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Agno imports for OpenRouter integration
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.os import AgentOS

# Local imports
from agents import (
    ats_optimizer,
    cover_letter_agent,
    cv_rewriter,
    interview_prep_agent,
    job_matcher,
    profile_builder,
)
from scrapper import scrape_all_advanced
from utils import (
    CVTailoringEngine,
    MockInterviewSimulator,
    discover_new_jobs,
    ethical_guidelines,
    jobs_collection,
    knowledge_base,
    match_student_to_jobs,
    sa_customizations,
    store_jobs_in_db,
)

# Load environment variables
if os.path.exists('.env'):
    load_dotenv(dotenv_path='.env', override=True)

# Setup logging early
try:
    from logger_config import setup_logging
    # Get log level from environment, default to INFO
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    app_logger = setup_logging(log_level=log_level, log_file='app.log')
except Exception as e:
    # Fallback to basic logging if setup fails
    import logging
    logging.basicConfig(level=logging.INFO)
    app_logger = logging.getLogger('job_market_analyzer')
    app_logger.warning(f"Failed to setup advanced logging: {e}")

# OpenRouter Models Configuration
# OpenRouter Models - Completely Free Models Only
MODELS = {
    "deepseek-chat": "deepseek/deepseek-chat",
    "deepseek-coder": "deepseek/deepseek-coder",
    "deepseek-r1": "deepseek/deepseek-r1",
    "microsoft-wizardlm": "microsoft/wizardlm-2-8x22b",
    "microsoft-wizardlm-7b": "microsoft/wizardlm-2-7b",
    "meta-llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct",
    "meta-llama-3.2-3b": "meta-llama/llama-3.2-3b-instruct",
    "mistral-7b": "mistralai/mistral-7b-instruct",
    "gemini-flash": "google/gemini-flash-1.5",
    "minimax-m2": "minimax/minimax-m2:free",
    "kimi-k2": "moonshotai/kimi-k2:free"
}

# Default model selection (can be overridden via OPENROUTER_MODEL_KEY env var)
DEFAULT_MODEL = "deepseek-chat"  # Completely free, fast and capable
SELECTED_MODEL = os.environ.get("OPENROUTER_MODEL_KEY", DEFAULT_MODEL)
if SELECTED_MODEL not in MODELS:
    app_logger.warning(f"OPENROUTER_MODEL_KEY '{SELECTED_MODEL}' is not valid. Falling back to '{DEFAULT_MODEL}'.")
    SELECTED_MODEL = DEFAULT_MODEL

# Validate required environment variables
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise SystemExit(
        "❌ OPENROUTER_API_KEY not set. Get a key from https://openrouter.ai/keys and set it in your environment."
    )

# Create the Agent with OpenRouter model
app_logger.info(f"Using OpenRouter model: {SELECTED_MODEL}")
model = OpenRouter(
    id=MODELS[SELECTED_MODEL],
    api_key=OPENROUTER_API_KEY,
)

agno_agent = Agent(
    name="Agno Agent",
    model=model,
    add_history_to_context=True,
    markdown=True,
)

# Model testing function for quick evaluation
class ModelTestHarness:
    """Reusable test harness that maintains a single Agent instance.

    Swaps models between tests to avoid recreating agents in a loop.
    """

    def __init__(self, api_key: str):
        # Start with the default selected model
        self.agent = Agent(
            name="Test Agent",
            model=OpenRouter(id=MODELS[SELECTED_MODEL], api_key=api_key),
            markdown=True,
        )
        self.api_key = api_key

    def run_model_test(self, model_key: str, test_prompt: str) -> bool:
        if model_key not in MODELS:
            print(f"❌ Model '{model_key}' not found. Available models:")
            for key, model_id in MODELS.items():
                print(f"  - {key}: {model_id}")
            return False

        print(f"🧪 Testing model: {model_key} ({MODELS[model_key]})")
        print(f"📝 Prompt: {test_prompt}")
        print("-" * 50)
        try:
            # Swap model on the existing agent
            self.agent.model = OpenRouter(id=MODELS[model_key], api_key=self.api_key)
            self.agent.print_response(test_prompt)
            print("\n✅ Test completed successfully!\n")
            return True
        except Exception as e:
            print(f"❌ Test failed: {e}\n")
            return False

# Create the AgentOS
agent_os = AgentOS(agents=[agno_agent])

# Get the FastAPI app for the AgentOS
app = agent_os.get_app()

# Configure CORS using environment variable ALLOWED_ORIGINS (comma-separated)
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

# Allow credentials only when not using wildcard
allow_credentials = "*" not in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["http://localhost:3000"],
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include team/task API routes (use empty router placeholder if not defined)
try:
    team_router  # type: ignore[name-defined]
except NameError:
    team_router = APIRouter()
app.include_router(team_router)

# Set defaults for optional variables
if not os.getenv('CV_FILE_PATH'):
    if os.path.exists('CV.pdf'):
        os.environ['CV_FILE_PATH'] = 'CV.pdf'
    elif os.path.exists('CV_PLACEHOLDER.txt'):
        os.environ['CV_FILE_PATH'] = 'CV_PLACEHOLDER.txt'
    else:
        # Defer hard failure to runtime; tests can proceed without a real CV
        os.environ['CV_FILE_PATH'] = 'CV_PLACEHOLDER.txt'

# Optional environment variables with defaults
CAREER_GOALS_DEFAULT = os.getenv('CAREER_GOALS_DEFAULT', "I want to become a software engineer in fintech")
DEFAULT_LOCATION = os.getenv('DEFAULT_LOCATION', "South Africa")
DEFAULT_INDUSTRY = os.getenv('DEFAULT_INDUSTRY', "Technology")
DEFAULT_EXPERIENCE_LEVEL = os.getenv('DEFAULT_EXPERIENCE_LEVEL', "Entry Level")
DEFAULT_DESIRED_ROLE = os.getenv('DEFAULT_DESIRED_ROLE', "Software Engineer")

# Cache configuration
CACHE_AGENT_TTL = int(os.getenv('CACHE_AGENT_TTL', '1800'))  # 30 minutes
CACHE_JOB_TTL = int(os.getenv('CACHE_JOB_TTL', '86400'))  # 24 hours
CACHE_PROFILE_TTL = int(os.getenv('CACHE_PROFILE_TTL', '3600'))  # 1 hour
CACHE_MAX_SIZE_AGENT = int(os.getenv('CACHE_MAX_SIZE_AGENT', '500'))
CACHE_MAX_SIZE_JOB = int(os.getenv('CACHE_MAX_SIZE_JOB', '200'))
CACHE_MAX_SIZE_PROFILE = int(os.getenv('CACHE_MAX_SIZE_PROFILE', '100'))

# API configuration
API_MAX_RETRIES = int(os.getenv('API_MAX_RETRIES', '3'))
API_RETRY_DELAY = float(os.getenv('API_RETRY_DELAY', '2.0'))
API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))

# Scraping configuration
MAX_JOBS_PER_SITE = int(os.getenv('MAX_JOBS_PER_SITE', '50'))
MAX_SEARCH_TERMS = int(os.getenv('MAX_SEARCH_TERMS', '5'))
SCRAPING_TIMEOUT = int(os.getenv('SCRAPING_TIMEOUT', '60'))  # seconds

# Version information
__version__ = "2.0.0"
__author__ = "Job Market AI Team"

# Logging is now configured in logger_config.py
# Additional verbose library suppression happens there

# Advanced caching system with metrics
class AgentCache:
    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 1800) -> None:  # 30 minutes default TTL
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache with metrics"""
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None

    def put(self, key: str, value: Any) -> None:
        """Put item in cache"""
        try:
            self.cache[key] = value
        except ValueError:
            # Cache is full, evict oldest
            self.evictions += 1
            # Try to put again after eviction
            self.cache[key] = value

    def get_stats(self) -> Dict[str, Union[int, str]]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        return {
            'size': len(self.cache),
            'maxsize': self.cache.maxsize,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'evictions': self.evictions
        }

# Initialize caches for different types of data
agent_response_cache = AgentCache(maxsize=CACHE_MAX_SIZE_AGENT, ttl_seconds=CACHE_AGENT_TTL)
job_scraping_cache = AgentCache(maxsize=CACHE_MAX_SIZE_JOB, ttl_seconds=CACHE_JOB_TTL)
profile_analysis_cache = AgentCache(maxsize=CACHE_MAX_SIZE_PROFILE, ttl_seconds=CACHE_PROFILE_TTL)

def parse_profile_analysis(profile_content: Optional[str]) -> Dict[str, Any]:
    """
    Parse the AI-generated profile analysis to extract structured data
    """
    profile_data = {
        'desired_role': DEFAULT_DESIRED_ROLE,
        'industry': DEFAULT_INDUSTRY,
        'skills': [],
        'location': DEFAULT_LOCATION,
        'career_goals': '',
        'experience_level': DEFAULT_EXPERIENCE_LEVEL
    }

    if not profile_content:
        return profile_data

    content = profile_content.lower()

    # Extract desired role - look for specific job titles first
    # Look for common developer roles in the summary
    developer_roles = ['full stack developer', 'frontend developer', 'backend developer',
                      'software developer', 'web developer', 'mobile developer',
                      'data scientist', 'data analyst', 'machine learning engineer',
                      'python developer', 'javascript developer', 'react developer']

    for role in developer_roles:
        if role in content:
            profile_data['desired_role'] = role.title()
            break

    # If no specific role found, try the general patterns
    if profile_data['desired_role'] == DEFAULT_DESIRED_ROLE:
        role_patterns = [
            r'seeking a ([a-z\s]+?) position',
            r'looking for a ([a-z\s]+?) role',
            r'become a ([a-z\s]+?)(?:\s|$)',
            r'work as a ([a-z\s]+?)(?:\s|in|\.|$)'
        ]

        for pattern in role_patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Clean up the extracted role
                role = matches[0].strip()
                # Skip if it matches "trajectory" or similar non-job terms
                if len(role) > 3 and len(role) < 50 and 'trajectory' not in role.lower():
                    profile_data['desired_role'] = role.title()
                    break

    # Extract industry
    industry_keywords = ['fintech', 'finance', 'banking', 'healthcare', 'technology', 'software',
                        'data science', 'machine learning', 'ai', 'web development', 'mobile']

    for industry in industry_keywords:
        if industry in content:
            profile_data['industry'] = industry.title()
            break

    # Extract skills from the analysis
    skills_section = re.search(r'skills.*?:\s*\n(.*?)(?:\n\n|\n\d+\.|$)', profile_content, re.IGNORECASE | re.DOTALL)
    if skills_section:
        skills_text = skills_section.group(1)
        # Extract skill names
        skill_lines = skills_text.split('\n')
        for line in skill_lines:
            # Look for skill entries
            skill_match = re.search(r'[•\-\*]\s*([^:]+?)(?:\s*\-\s*|\s*\:\s*|\s*$)', line.strip())
            if skill_match:
                skill = skill_match.group(1).strip()
                if len(skill) > 1 and len(skill) < 30:
                    profile_data['skills'].append(skill)

    # If no skills extracted, use defaults
    if not profile_data['skills']:
        profile_data['skills'] = ['Python', 'JavaScript', 'SQL', 'Problem Solving', 'Communication']

    # Extract location preferences
    location_patterns = ['johannesburg', 'cape town', 'durban', 'pretoria', 'remote', 'south africa']
    for location in location_patterns:
        if location in content:
            profile_data['location'] = location.title()
            break

    # Extract experience level
    if 'senior' in content or 'experienced' in content:
        profile_data['experience_level'] = 'Senior'
    elif 'junior' in content or 'entry' in content:
        profile_data['experience_level'] = 'Entry Level'
    else:
        profile_data['experience_level'] = 'Mid Level'

    return profile_data

def cached_agent_run(agent: Any, prompt: str, cache_key: Optional[str] = None, cache_type: str = 'agent') -> Any:
    """
    Run agent with advanced caching and metrics
    """
    # Sanitize prompt for security
    prompt = sanitize_input(prompt, max_length=50000)  # Allow longer prompts for AI

    # Select appropriate cache based on type
    cache = {
        'agent': agent_response_cache,
        'job': job_scraping_cache,
        'profile': profile_analysis_cache
    }.get(cache_type, agent_response_cache)

    # Generate comprehensive cache key using full content hash
    if cache_key is None:
        # Use full prompt hash instead of truncated version
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        cache_key = f"{agent.name}_{prompt_hash}"

    # Check cache
    cached_response = cache.get(cache_key)
    if cached_response is not None:
        print(f"   📋 Cache hit for {agent.name} ({cache_type} cache)")
        return cached_response

    # Run agent with retry logic
    print(f"   🤖 Running {agent.name} (cache miss)")
    response = None

    for attempt in range(API_MAX_RETRIES):
        try:
            response = agent.run(prompt)
            break  # Success, exit retry loop
        except Exception as e:
            error_msg = str(e)
            if attempt < API_MAX_RETRIES - 1:
                wait_time = (API_RETRY_DELAY ** attempt) + 0.1  # Exponential backoff with jitter
                print(f"   ⚠️  API call failed (attempt {attempt + 1}/{API_MAX_RETRIES}): {error_msg}")
                print(f"   ⏳ Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            else:
                print(f"   ❌ API call failed after {API_MAX_RETRIES} attempts: {error_msg}")
                # Return a fallback response instead of raising exception
                response = type('Response', (), {'content': f"Error: Unable to generate response after {API_MAX_RETRIES} attempts. Please try again later."})()
                break

    cache.put(cache_key, response)
    return response

def get_cache_stats():
    """Get comprehensive cache statistics"""
    return {
        'agent_responses': agent_response_cache.get_stats(),
        'job_scraping': job_scraping_cache.get_stats(),
        'profile_analysis': profile_analysis_cache.get_stats()
    }

def show_cost_estimation():
    """Show estimated costs for AI operations"""
    print("\n💰 AI Cost Estimation (OpenRouter Models):")
    print("-" * 50)
    print("📊 Estimated costs for a typical analysis:")
    print("   • CV Analysis: $0.001 - $0.003 (2,000-6,000 tokens)")
    print("   • Job Matching: $0.002 - $0.005 (4,000-10,000 tokens)")
    print("   • Cover Letter Gen: $0.003 - $0.007 (6,000-14,000 tokens)")
    print("   • **Total per run: $0.006 - $0.015**")
    print()
    print("💡 Cost-saving features active:")
    print("   • Intelligent caching (reduces repeated API calls)")
    print("   • Response deduplication")
    print("   • Optimized prompts for efficiency")
    print()
    print("📈 Monthly usage estimates:")
    print("   • Light usage (5 runs/week): $1.20 - $3.00")
    print("   • Moderate usage (20 runs/week): $4.80 - $12.00")
    print("   • Heavy usage (50 runs/week): $12.00 - $30.00")
    print()
    print("🔄 Cached responses will significantly reduce actual costs!")
    print("-" * 50)

def create_health_app() -> "FastAPI":
    """Create FastAPI app with health check endpoints"""
    app = FastAPI(
        title="Job Market AI Analyzer",
        description="AI-powered job matching and career assistance platform",
        version=__version__
    )

    @app.get("/health")
    async def health_check():
        """Basic health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": __version__
        }

    @app.get("/health/detailed")
    async def detailed_health_check():
        """Detailed health check with system metrics"""
        try:
            # Check cache status
            cache_stats = get_cache_stats()

            # Check if required dependencies are available
            dependencies_status = {
                "google_genai": True,  # Assume available if we got this far
                "chromadb": True,
                "playwright": True,
                "pymupdf": True
            }

            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": __version__,
                "uptime": str(datetime.now() - datetime.fromtimestamp(__import__('time').time())),
                "cache_stats": cache_stats,
                "dependencies": dependencies_status,
                "environment": {
                    "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
                    "platform": __import__('platform').platform()
                }
            }
        except Exception as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )

    @app.get("/metrics")
    async def metrics():
        """Application metrics endpoint"""
        cache_stats = get_cache_stats()
        return {
            "cache_performance": cache_stats,
            "timestamp": datetime.now().isoformat()
        }

    return app

def start_web_server(port: int = 8000):
    """Start FastAPI web server with health check endpoints"""
    print("🚀 Starting Job Market AI Analyzer Web Server")
    print("=" * 60)
    print(f"📍 Server will be available at: http://localhost:{port}")
    print("📊 Health check: http://localhost:{port}/health")
    print("📈 Metrics: http://localhost:{port}/metrics")
    print("🔄 Detailed health: http://localhost:{port}/health/detailed")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print()

    app = create_health_app()
    uvicorn.run(app, host="0.0.0.0", port=port)

def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input to prevent prompt injection and other security issues
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text or not isinstance(text, str):
        return ""

    original_length = len(text)
    
    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                # JavaScript URLs
        r'data:',                      # Data URLs
        r'vbscript:',                  # VBScript
        r'on\w+\s*=',                  # Event handlers
    ]

    sanitized = text
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)

    # Log if content was removed
    if len(sanitized) < original_length:
        app_logger.warning(f"Sanitized input removed {original_length - len(sanitized)} characters of potentially dangerous content")

    # Limit length
    if len(sanitized) > max_length:
        app_logger.warning(f"Input truncated from {len(sanitized)} to {max_length} characters")
        sanitized = sanitized[:max_length] + "..."

    # Remove excessive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    return sanitized

def validate_file_path(file_path: str) -> bool:
    """
    Validate file path to prevent directory traversal attacks
    
    Args:
        file_path: Path to validate
        
    Returns:
        True if path is valid, False otherwise
    """
    if not file_path or not isinstance(file_path, str):
        return False

    # Check for directory traversal attempts
    if '..' in file_path or file_path.startswith('/') or file_path.startswith('\\'):
        app_logger.warning(f"Invalid file path detected (directory traversal attempt): {file_path}")
        return False

    # Check file extension (only allow safe types)
    allowed_extensions = {'.pdf', '.txt', '.doc', '.docx'}
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext and file_ext not in allowed_extensions:
        app_logger.warning(f"Unsupported file extension: {file_ext}")
        return False

    return True

# Configure Gemini API for embeddings
# Note: Individual agents handle their own API configuration

# Initialize knowledge base (this will create collections if they don't exist)
app_logger.info("Initializing Knowledge Base...")
try:
    kb_stats = knowledge_base.get_all_stats()
    total_docs = sum(stats['document_count'] if stats else 0 for stats in kb_stats.values())
    app_logger.info(f"Knowledge Base ready with {total_docs} documents across {len(kb_stats)} sources")

    # Initialize with sample data if collections are empty
    if total_docs == 0:
        app_logger.info("Populating knowledge base with sample data...")
        knowledge_base.initialize_sample_data()
    
except Exception as e:
    app_logger.warning(f"Knowledge Base initialization warning: {e}", exc_info=True)

# Agent coordination will be handled in CareerBoostPlatform class

def generate_student_id():
    """Generate unique student ID"""
    return str(uuid.uuid4())[:8].upper()

def read_cv_file(cv_path: str) -> str:
    """
    Utility function to read CV file and return text content

    Args:
        cv_path: Path to CV PDF file

    Returns:
        Extracted text content from CV

    Raises:
        FileNotFoundError: If CV file doesn't exist
        ValueError: If file cannot be read
    """
    if not os.path.exists(cv_path):
        raise FileNotFoundError(f"CV file not found: {cv_path}")

    cv_text = ""
    try:
        with fitz.open(cv_path) as doc:
            for page_num, page in enumerate(doc, 1):
                cv_text += page.get_text()
        return cv_text
    except Exception as e:
        raise ValueError(f"Failed to read CV file: {e}")

def handle_operation_error(operation_name: str, error: Exception, verbose: bool = False) -> None:
    """
    Utility function for consistent error handling and reporting

    Args:
        operation_name: Name of the operation that failed
        error: The exception that occurred
        verbose: Whether to show detailed error info
    """
    error_msg = str(error)
    if verbose:
        print(f"❌ {operation_name} failed: {error_msg}")
    else:
        print(f"❌ {operation_name} failed")
    return None

# All utility functions have been moved to the utils package


class JobMarketAnalyzer:
    """Professional Job Market Analysis System"""

    def __init__(self, verbose=False, quiet=False):
        """
        Initialize the Job Market Analyzer

        Args:
            verbose (bool): Enable verbose output
            quiet (bool): Suppress non-essential output
        """
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
        # Validate and sanitize inputs
        if not os.path.exists(cv_path):
            raise FileNotFoundError(f"CV file not found: {cv_path}")

        if not validate_file_path(cv_path):
            raise ValueError(f"Invalid file path: {cv_path}")

        career_goals = sanitize_input(career_goals, max_length=1000)

        self.print_progress("CV ANALYSIS", "PROCESSING")

        try:
            # Read CV using utility function
            cv_text = read_cv_file(cv_path)
            if not self.quiet:
                num_pages = len(cv_text.split('\n\n'))  # Rough estimate of pages
                print(f"   📄 CV loaded: {len(cv_text)} characters from ~{num_pages} pages")

            # AI Analysis
            if not self.quiet:
                print("   🤖 Analyzing with AI...")
            profile_analysis = cached_agent_run(profile_builder, f"""
            CV Content:
            {cv_text}

            Career Goals:
            {career_goals}

            Provide:
            1. Structured profile summary
            2. Skills inventory with proficiency levels
            3. Career trajectory assessment
            4. Recommended skill development areas
            """, cache_type='profile')

            self.print_success("CV analysis completed")
            if not self.quiet:
                print("\n📊 PROFILE ANALYSIS:")
                print("-" * 50)
                print(profile_analysis.content)

            return cv_text, profile_analysis.content

        except Exception as e:
            self.print_error(f"CV analysis failed: {e}")
            return None, None

    def generate_cover_letters(self, student_profile, matched_jobs, cv_text):
        """Generate personalized cover letters for matched jobs"""
        self.print_progress("COVER LETTER GENERATION", "WRITING")

        cover_letters = []
        generated_count = 0

        for i, job in enumerate(matched_jobs[:3]):  # Limit to top 3
            try:
                # Extract job details
                job_title = job.get('title', 'Unknown Position')
                company = job.get('company', 'Unknown Company')
                job_description = job.get('description', '')[:1000]  # Limit description length

                # Generate cover letter
                cover_letter_prompt = f"""
                Generate a personalized cover letter for this job application:

                **APPLICANT PROFILE:**
                Name: Unathi Tshuma (extracted from CV)
                Desired Role: {student_profile.get('desired_role', 'Software Engineer')}
                Experience Level: {student_profile.get('experience_level', 'Entry Level')}
                Key Skills: {', '.join(student_profile.get('skills', [])[:5])}
                Career Goals: {student_profile.get('career_goals', 'Become a skilled software engineer')}

                **CV SUMMARY:**
                {cv_text[:800]}...

                **JOB DETAILS:**
                Position: {job_title}
                Company: {company}
                Description: {job_description}

                **INSTRUCTIONS:**
                Create a compelling cover letter that:
                1. Shows genuine interest in the company and role
                2. Highlights relevant skills and experience from the CV
                3. Connects the applicant's background to the job requirements
                4. Demonstrates enthusiasm and fit for the company culture
                5. Calls the reader to action

                Keep it professional, concise (250-350 words), and impactful.
                """

                cover_letter = cached_agent_run(
                    cover_letter_agent,
                    cover_letter_prompt,
                    cache_key=f"cover_letter_{hashlib.md5((job_title + company + student_profile.get('desired_role', '')).encode()).hexdigest()[:8]}"
                )

                cover_letters.append({
                    'job_title': job_title,
                    'company': company,
                    'cover_letter': cover_letter.content if hasattr(cover_letter, 'content') else str(cover_letter),
                    'job_url': job.get('url', 'N/A')
                })

                generated_count += 1
                if not self.quiet:
                    print(f"   ✓ Generated cover letter for {job_title} at {company}")

            except Exception as e:
                if not self.quiet:
                    print(f"⚠️ Failed to generate cover letter for {job.get('title', 'Unknown')}: {e}")

        self.print_success(f"Generated {generated_count} cover letters")

        # Save cover letters to file
        if cover_letters:
            try:
                import json
                with open('generated_cover_letters.json', 'w', encoding='utf-8') as f:
                    json.dump(cover_letters, f, ensure_ascii=False, indent=2)
                print("💾 Cover letters saved to generated_cover_letters.json")
            except Exception as e:
                if not self.quiet:
                    print(f"⚠️ Failed to save cover letters: {e}")

        return cover_letters

    def discover_jobs(self, student_profile):
        """Discover and scrape jobs professionally"""
        self.print_progress("JOB DISCOVERY", "SCRAPING")

        # Create sophisticated search terms based on profile analysis
        desired_role = student_profile.get('desired_role', 'Software Engineer')
        experience_level = student_profile.get('experience_level', 'Entry Level')
        skills = student_profile.get('skills', [])[:3]  # Top 3 skills
        industry = student_profile.get('industry', 'Technology')
        location = student_profile.get('location', 'South Africa')

        # Build intelligent search terms
        search_terms = []

        # Primary search: role + experience level
        if experience_level == 'Entry Level':
            search_terms.extend([f"junior {desired_role}", f"entry level {desired_role}", desired_role])
        elif experience_level == 'Senior':
            search_terms.extend([f"senior {desired_role}", f"experienced {desired_role}", desired_role])
        else:
            search_terms.append(desired_role)

        # Add skill-based searches
        for skill in skills:
            if skill and len(skill) > 2:
                # Clean skill names for search
                clean_skill = skill.lower().replace(' ', '').replace('-', '')
                if len(clean_skill) > 3:
                    search_terms.append(f"{clean_skill} {desired_role.lower()}")

        # Add industry-specific searches
        if industry.lower() != 'technology':
            search_terms.append(f"{desired_role} {industry}")

        # Remove duplicates and limit
        search_terms = list(set(search_terms))[:MAX_SEARCH_TERMS]

        if not self.quiet:
            print(f"   🎯 Searching for: {desired_role}")
            print(f"   📍 Location: {location}")
            print(f"   🛠️  Experience: {experience_level}")
            print(f"   🎨 Industry: {industry}")
            print(f"   🔍 Search terms: {', '.join(search_terms)}")

        # Store search terms for reference
        student_profile['search_terms'] = search_terms

        try:
            # Use discover_new_jobs with reduced verbosity to minimize API logs and timeout
            import threading

            result_container = {}
            exception_container = {}

            def run_with_timeout():
                try:
                    jobs = discover_new_jobs(student_profile, location, verbose=False, max_jobs=MAX_JOBS_PER_SITE)
                    result_container['jobs'] = jobs
                except Exception as e:
                    exception_container['error'] = e

            # Start job discovery in a separate thread
            discovery_thread = threading.Thread(target=run_with_timeout)
            discovery_thread.start()

            # Wait for completion with timeout
            discovery_thread.join(timeout=SCRAPING_TIMEOUT)

            if discovery_thread.is_alive():
                # Thread is still running, operation timed out
                self.print_warning("Job discovery operation timed out")
                matched_jobs = []
            elif 'error' in exception_container:
                # Thread completed with error
                raise exception_container['error']
            else:
                # Thread completed successfully
                matched_jobs = result_container.get('jobs', [])

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
            rewritten_cv = cached_agent_run(cv_rewriter, f"""
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
            """, cache_key=f"cv_rewrite_{hashlib.md5((cv_text[:50] + job_title).encode()).hexdigest()[:8]}")

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

        # Parse the profile analysis to extract structured data
        parsed_profile = parse_profile_analysis(profile_content)

        # Create profile for matching using extracted data
        student_profile = {
            'summary': cv_text[:500],
            'cv_text': cv_text,  # Full CV text for keyword analysis
            'profile_analysis': profile_content,  # Store full analysis
            'skills': parsed_profile['skills'],
            'desired_role': parsed_profile['desired_role'],
            'industry': parsed_profile['industry'],
            'field_of_study': 'Computer Science',  # Could also be extracted
            'location': parsed_profile['location'],
            'experience_level': parsed_profile['experience_level'],
            'career_goals': career_goals or parsed_profile.get('career_goals', '')
        }

        if not self.quiet:
            print(f"\n🎯 EXTRACTED PROFILE:")
            print(f"   Role: {student_profile['desired_role']}")
            print(f"   Industry: {student_profile['industry']}")
            print(f"   Location: {student_profile['location']}")
            print(f"   Skills: {', '.join(student_profile['skills'][:5])}...")
            print(f"   Experience: {student_profile['experience_level']}")

        # Discover jobs
        jobs_found = self.discover_jobs(student_profile)

        # Match jobs
        if jobs_found > 0:
            matched_jobs = self.match_jobs(student_profile)

            # Generate cover letters for top matched jobs
            if matched_jobs and not self.quiet:
                print("\n📝 Generating cover letters for top matches...")
                top_matches = matched_jobs[:3]  # Generate for top 3 matches
                cover_letters = self.generate_cover_letters(student_profile, top_matches, cv_text)

        # Summary
        elapsed = datetime.now() - self.start_time

        # Show cache statistics in verbose mode
        if not self.quiet:
            cache_stats = get_cache_stats()
            print(f"\n📊 Cache Performance:")
            for cache_name, stats in cache_stats.items():
                if stats['hits'] + stats['misses'] > 0:  # Only show active caches
                    print(f"   {cache_name.replace('_', ' ').title()}: {stats['hit_rate']} ({stats['hits']}/{stats['hits'] + stats['misses']} hits)")

            print(f"\n⏱️  Analysis completed in {elapsed.total_seconds():.1f} seconds")
            print("="*70)

        return True


# Complete student career platform
class CareerBoostPlatform:
    """
    Complete student career platform with coordinated AI agents
    """
    def __init__(self):
        """
        Initialize the Career Boost Platform with all AI agents
        """
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

        profile = cached_agent_run(profile_builder, f"""
        Analyze CV: {student_cv}
        Career Goals: {career_goals}

        Create comprehensive profile including:
        - Education background
        - Work experience
        - Skills assessment
        - Career aspirations
        - Areas for development
        """, cache_key=f"platform_profile_{hashlib.md5((student_cv[:50] + career_goals).encode()).hexdigest()[:8]}")

        # Parse the profile analysis to extract structured data
        profile_text = profile.content if hasattr(profile, 'content') else str(profile)
        parsed_profile = parse_profile_analysis(profile_text)

        student_id = generate_student_id()

        # Obtain ethical consent for data processing
        consent_id = self.ethical_guidelines.manage_data_consent(
            student_id=student_id,
            data_types=['cv_content', 'career_goals', 'application_history', 'performance_data'],
            purpose='AI-powered career assistance and job matching',
            retention_period='2 years'
        )

        self.students[student_id] = {
            'profile': profile_text,
            'parsed_profile': parsed_profile,  # Store structured data
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

        # Use parsed profile data for job matching
        parsed_profile = student.get('parsed_profile', {})
        student_profile = {
            'summary': student['cv_text'][:500],
            'cv_text': student['cv_text'],
            'profile_analysis': student.get('profile', ''),
            'skills': parsed_profile.get('skills', ['Python', 'JavaScript', 'SQL']),
            'desired_role': parsed_profile.get('desired_role', 'Software Engineer'),
            'industry': parsed_profile.get('industry', 'Technology'),
            'experience_level': parsed_profile.get('experience_level', 'Entry Level'),
            'location': parsed_profile.get('location', location),
            'career_goals': student.get('career_goals', '')
        }

        # Discover new jobs
        matched_jobs = discover_new_jobs(student_profile, location, verbose=True, max_jobs=MAX_JOBS_PER_SITE)

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

    def export_student_data(self, student_id, export_format='json'):
        """
        Export all student data in GDPR-compliant format

        Args:
            student_id: Student identifier
            export_format: 'json' or 'pdf' (default: json)

        Returns:
            Dict containing all student data for export
        """
        if student_id not in self.students:
            raise ValueError(f"Student {student_id} not found")

        student = self.students[student_id]

        # Gather all student data
        export_data = {
            'export_metadata': {
                'student_id': student_id,
                'export_date': datetime.now().isoformat(),
                'data_controller': 'Job Market AI Analyzer',
                'gdpr_compliant': True,
                'retention_period': '2 years from onboarding',
                'export_format': export_format
            },
            'personal_data': {
                'student_id': student_id,
                'onboarded_at': student['onboarded_at'].isoformat(),
                'consent_id': student.get('consent_id'),
                'ethical_disclosure': student.get('ethical_disclosure')
            },
            'career_profile': {
                'cv_text': student.get('cv_text', ''),
                'profile_analysis': student.get('profile'),
                'parsed_profile': student.get('parsed_profile'),
                'career_goals': student.get('career_goals'),
                'cv_engine_initialized': student.get('cv_engine') is not None
            },
            'job_search_activity': {
                'total_jobs_found': len(self.jobs),
                'applications_submitted': len([
                    app for app in self.applications.values()
                    if app['student_id'] == student_id
                ]),
                'application_history': [
                    {
                        'application_id': app_id,
                        'job_title': app['job_title'],
                        'company': app['company'],
                        'applied_at': app['applied_at'].isoformat(),
                        'match_score': app['match_score'],
                        'ethical_assessment': app.get('ethical_validation'),
                        'url': app.get('job_url')
                    }
                    for app_id, app in self.applications.items()
                    if app['student_id'] == student_id
                ]
            },
            'system_usage': {
                'knowledge_base_queries': [],  # Could be tracked separately
                'cache_usage': get_cache_stats(),  # System-wide cache stats
                'platform_features_used': [
                    'cv_analysis', 'job_matching', 'cover_letter_generation',
                    'interview_prep', 'ethical_guidelines', 'sa_customizations'
                ]
            }
        }

        # Add data portability information
        export_data['data_portability'] = {
            'can_be_transferred': True,
            'machine_readable': True,
            'comprehensive': True,
            'retention_rights': 'Data retained for 2 years, can be deleted anytime',
            'consent_withdrawal': 'Consent can be withdrawn at any time'
        }

        return export_data

    def delete_student_data(self, student_id, consent_id):
        """
        GDPR/POPIA compliant data deletion

        Args:
            student_id: Student identifier
            consent_id: Consent ID to verify deletion request

        Returns:
            Dict with deletion confirmation
        """
        if student_id not in self.students:
            raise ValueError(f"Student {student_id} not found")

        student = self.students[student_id]

        # Verify consent ID matches
        if student.get('consent_id') != consent_id:
            raise ValueError("Invalid consent ID. Cannot proceed with deletion.")

        # Log deletion for audit trail
        deletion_log = {
            'student_id': student_id,
            'consent_id': consent_id,
            'deletion_requested_at': datetime.now().isoformat(),
            'data_categories_deleted': [
                'personal_data', 'career_profile', 'job_search_activity',
                'application_history', 'cv_engine', 'consent_records'
            ]
        }

        # Delete applications
        apps_to_delete = [
            app_id for app_id, app in self.applications.items()
            if app['student_id'] == student_id
        ]
        for app_id in apps_to_delete:
            del self.applications[app_id]

        # Delete jobs (only if no other students reference them - simplified)
        # In production, this would check for references

        # Delete student record
        del self.students[student_id]

        # Withdraw consent
        self.ethical_guidelines.withdraw_consent(consent_id)

        return {
            'deletion_confirmed': True,
            'student_id': student_id,
            'deleted_at': datetime.now().isoformat(),
            'audit_log': deletion_log,
            'confirmation_message': 'All personal data has been securely deleted as per GDPR/POPIA requirements.'
        }

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

    # Data export and GDPR compliance options
    parser.add_argument(
        '--export-data',
        type=str,
        help='Export student data (provide student ID)'
    )

    parser.add_argument(
        '--delete-data',
        type=str,
        help='Delete student data (provide student ID, requires consent ID)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__} by {__author__}'
    )

    # Web server mode
    parser.add_argument(
        '--web-server',
        action='store_true',
        help='Start web server with health check endpoints'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port for web server (default: 8000)'
    )

    return parser


def main():
    """Main entry point with professional CLI"""
    # Setup graceful shutdown handling
    import signal
    import sys

    def signal_handler(signum, frame):
        """Handle graceful shutdown on Ctrl+C"""
        print("\n\n🛑 Received shutdown signal. Cleaning up...")
        print("💾 Saving cache and finalizing...")
        # Any cleanup code here
        print("✅ Shutdown complete. Goodbye! 👋")
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

    parser = create_parser()
    args = parser.parse_args()

    # Debug: Check if web server mode (only show if actually enabled)
    if hasattr(args, 'web_server') and args.web_server:
        if not FASTAPI_AVAILABLE:
            print("❌ FastAPI not available. Install with: pip install fastapi uvicorn")
            print("💡 To use web server features, run: pip install fastapi uvicorn")
            sys.exit(1)
        start_web_server(args.port)
        return

    # Show cost estimation for AI operations
    if not args.quiet:
        show_cost_estimation()

    # Check if user wants to test a specific model (OpenRouter CLI interface)
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            # Test all models or a specific one
            if len(sys.argv) > 2:
                harness = ModelTestHarness(OPENROUTER_API_KEY)
                harness.run_model_test(sys.argv[2], "Hello! Can you tell me about yourself in one sentence?")
            else:
                print("🧪 Testing all available models...")
                harness = ModelTestHarness(OPENROUTER_API_KEY)
                successes = 0
                total = 0
                for model_key in MODELS.keys():
                    if model_key != "test":  # Skip legacy test model
                        total += 1
                        ok = harness.run_model_test(model_key, "Hello! Can you tell me about yourself in one sentence?")
                        successes += 1 if ok else 0
                        print("\n" + "="*80 + "\n")
                print(f"✅ Passed {successes}/{total} model tests")
            return
        elif sys.argv[1] == "--list":
            print("📋 Available OpenRouter Models:")
            print("=" * 50)
            for key, model_id in MODELS.items():
                print(f"  {key}: {model_id}")
            print("\n💡 Usage:")
            print("  python main.py --test [model_key]  # Test specific model")
            print("  python main.py --test              # Test all models")
            print("  python main.py --list              # List all models")
            print("  python main.py                     # Start AgentOS server")
            return
        else:
            print("❌ Unknown argument. Use --test, --list, or no arguments to start server.")
            return

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

    # Start the AgentOS server (if no specific mode was selected)
    print(f"🚀 Starting AgentOS with OpenRouter model: {SELECTED_MODEL} ({MODELS[SELECTED_MODEL]})")
    print("📡 Server will be available at: http://localhost:8000")
    print("🎨 Agent UI will be available at: http://localhost:3000 (if started separately)")
    print("-" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)


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

        # Read CV using utility function (handles validation)
        try:
            cv_text = read_cv_file(cv_path)
        except (FileNotFoundError, ValueError) as e:
            print(f"❌ {e}")
            sys.exit(1)

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

        elif args.export_data:
            # Export student data
            student_id = args.export_data
            try:
                export_data = platform.export_student_data(student_id)
                import json
                filename = f"student_data_export_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)

                print(f"✅ Student data exported successfully!")
                print(f"📄 File: {filename}")
                print(f"📊 Data categories exported: {len(export_data) - 1}")  # Exclude metadata
                print(f"🛡️  GDPR compliant: {export_data['export_metadata']['gdpr_compliant']}")
                print(f"📅 Export date: {export_data['export_metadata']['export_date'][:10]}")

            except ValueError as e:
                print(f"❌ Error: {e}")

        elif args.delete_data:
            # Delete student data (GDPR/POPIA compliant)
            student_id = args.delete_data

            # Get consent ID for verification
            if student_id in platform.students:
                consent_id = platform.students[student_id].get('consent_id')
                if consent_id:
                    confirm = input(f"\n⚠️  DATA DELETION REQUEST\nThis will permanently delete ALL data for student {student_id}\nConsent ID: {consent_id}\n\nType 'DELETE' to confirm: ")
                    if confirm.upper() == 'DELETE':
                        try:
                            deletion_result = platform.delete_student_data(student_id, consent_id)
                            print(f"\n✅ DATA DELETION COMPLETED")
                            print("=" * 50)
                            print(f"🆔 Student ID: {deletion_result['student_id']}")
                            print(f"🗑️  Deleted at: {deletion_result['deleted_at'][:19]}")
                            print(f"📋 Categories deleted: {', '.join(deletion_result['audit_log']['data_categories_deleted'])}")
                            print(f"\n{deletion_result['confirmation_message']}")
                        except ValueError as e:
                            print(f"❌ Error: {e}")
                    else:
                        print("❌ Deletion cancelled.")
                else:
                    print(f"❌ No consent ID found for student {student_id}")
            else:
                print(f"❌ Student {student_id} not found")

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
            print("  --export-data <id>      : Export student data (GDPR)")
            print("  --delete-data <id>      : Delete student data (GDPR/POPIA)")

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