"""
Profile Builder Agent
Analyzes student CVs and profiles to extract structured career information
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

# Create Profile Builder Agent
profile_builder = Agent(
    name="Profile Analyst",
    model=Gemini(id="gemini-2.0-flash"),
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

# Restore GEMINI_API_KEY if it was set
if gemini_key_backup:
    os.environ['GEMINI_API_KEY'] = gemini_key_backup
