"""
Job Matcher Agent
Matches students with job opportunities using multi-dimensional analysis
"""

import os
import logging
from agno.agent import Agent
from agno.tools.file import FileTools
from agno.models.openrouter import OpenRouter

# Configure logging
logging.getLogger('agno').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

# Function to create the agent with proper API key loading
def _create_job_matcher():
    """Create Job Matcher Agent with proper API key loading"""
    # Import cached API key from main module
    try:
        from main import _OPENROUTER_API_KEY
        OPENROUTER_API_KEY = _OPENROUTER_API_KEY
    except ImportError:
        # Fallback to environment loading if main module not available
        OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found. Please set it in environment or .env file")

    return Agent(
        name="Job Matching Specialist",
        model=OpenRouter(id="deepseek/deepseek-chat", api_key=OPENROUTER_API_KEY),
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

# Create the job matcher instance
job_matcher = _create_job_matcher()
