"""
Interview Coach Agent
Generates realistic interview questions based on job postings and student profiles
"""

import os
import logging
from agno.agent import Agent
from agno.models.google import Gemini

# Configure logging
logging.getLogger('google.genai').setLevel(logging.WARNING)
logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('agno').setLevel(logging.WARNING)

# Suppress API key confirmation messages by temporarily unsetting conflicting env vars
gemini_key_backup = os.environ.get('GEMINI_API_KEY')
if 'GEMINI_API_KEY' in os.environ:
    del os.environ['GEMINI_API_KEY']

# Create Interview Coach Agent
interview_prep_agent = Agent(
    name="Interview Coach",
    model=Gemini(id="gemini-2.0-flash"),
    instructions="""Generate realistic interview questions based on:

    1. JOB-SPECIFIC QUESTIONS:
       Technical: "Explain how you would design a database for X"
       Behavioral: "Tell me about a time you worked in a team"
       Role-specific: "How do you prioritize competing deadlines?"

    2. COMPANY-SPECIFIC QUESTIONS:
       - Research company values and ask related questions
       - Reference company projects: "What interests you about our work on X?"

    3. STUDENT BACKGROUND QUESTIONS:
       - Based on CV: "I see you worked on project X, tell me more"
       - Education: "How has your degree prepared you for this role?"
       - Gaps: "I notice you graduated 6 months ago, what have you been doing?"

    4. COMMON SOUTH AFRICAN CONTEXT:
       - Transport/location: "Can you reliably commute to our office?"
       - Work authorization: "Do you have right to work in South Africa?"
       - Salary expectations: "What are your salary expectations?"

    Generate 15-20 questions across categories:
    - 5 Technical/Skills-based
    - 5 Behavioral (STAR method)
    - 3 Company/Role-specific
    - 2 Background/CV questions
    - 3-5 Curveball/stress questions"""
)

# Restore GEMINI_API_KEY if it was set
if gemini_key_backup:
    os.environ['GEMINI_API_KEY'] = gemini_key_backup
