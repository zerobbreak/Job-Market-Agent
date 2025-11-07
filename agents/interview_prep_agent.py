"""
Interview Coach Agent
Generates realistic interview questions based on job postings and student profiles
"""

import os
import logging
from agno.agent import Agent
from agno.models.openrouter import OpenRouter

# Configure logging
logging.getLogger('agno').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

# Get OpenRouter API key - required for agent functionality
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    # Allow import for testing, but will fail when agent is actually used
    OPENROUTER_API_KEY = None

# Create Interview Coach Agent
# Note: Will raise error if OPENROUTER_API_KEY is not set when agent is used
interview_prep_agent = Agent(
    name="Interview Coach",
    model=OpenRouter(id="deepseek/deepseek-chat", api_key=OPENROUTER_API_KEY or "placeholder"),
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
