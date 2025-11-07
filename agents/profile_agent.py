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

# Get OpenRouter API key - required for agent functionality
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    # Allow import for testing, but will fail when agent is actually used
    OPENROUTER_API_KEY = None

# Create Profile Builder Agent
# Note: Will raise error if OPENROUTER_API_KEY is not set when agent is used
profile_builder = Agent(
    name="Profile Analyst",
    model=OpenRouter(id="deepseek/deepseek-chat", api_key=OPENROUTER_API_KEY or "placeholder"),
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
