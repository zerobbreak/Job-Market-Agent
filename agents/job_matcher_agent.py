"""
Job Matcher Agent
Matches students with job opportunities using multi-dimensional analysis
"""

import os
import logging
from agno.agent import Agent
from agno.tools.file import FileTools
from agno.models.google import Gemini

# Configure logging
logging.getLogger('google.genai').setLevel(logging.WARNING)
logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('agno').setLevel(logging.WARNING)

# Suppress API key confirmation messages by temporarily unsetting conflicting env vars
gemini_key_backup = os.environ.get('GEMINI_API_KEY')
if 'GEMINI_API_KEY' in os.environ:
    del os.environ['GEMINI_API_KEY']

# Create Job Matcher Agent
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
