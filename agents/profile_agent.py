"""
Profile Builder Agent
Analyzes student CVs and profiles to extract structured career information
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
def _create_profile_builder():
    """Create Profile Builder Agent with proper API key loading"""
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
        name="Profile Analyst",
        model=OpenRouter(id="deepseek/deepseek-chat", api_key=OPENROUTER_API_KEY),
        tools=[FileTools()],
        instructions="""Analyze student CVs and profiles to extract and compare against market demands:

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

GAP ANALYSIS:
- Compare skills against industry market demands
- Identify skill deficiencies and gaps
- Assess competitiveness in target roles
- Recommend specific skill development priorities

Create a structured profile with:
- Skill proficiency levels (beginner, intermediate, advanced)
- Market comparison and competitive positioning
- Experience gaps that need addressing
- Competitive advantages and unique selling points
- Specific recommendations for skill improvement
""",
    markdown=True
)

# Create the profile builder instance
profile_builder = _create_profile_builder()
