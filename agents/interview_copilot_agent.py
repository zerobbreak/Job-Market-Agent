"""
Interview Copilot Agent
Provides real-time subtle guidance during interviews (use responsibly)
"""

import os
import logging
from agno.agent import Agent
from agno.models.openrouter import OpenRouter

# Configure logging
logging.getLogger('agno').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

# Function to create the agent with proper API key loading
def _create_interview_copilot():
    """Create Interview Copilot Agent with proper API key loading"""
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
        name="Interview Assistant",
        model=OpenRouter(id="deepseek/deepseek-chat", api_key=OPENROUTER_API_KEY),
    instructions="""Provide real-time subtle guidance during interviews:

    ETHICAL USAGE:
    ✅ DO:
    - Provide gentle reminders of key talking points
    - Suggest structure (STAR method) for behavioral questions
    - Offer keywords to include in response
    - Help with technical concept clarification

    ❌ DON'T:
    - Generate complete answers for student to read verbatim
    - Fabricate experiences student doesn't have
    - Answer technical questions student can't answer

    OUTPUT FORMAT:
    - Bullet points (3-5 max)
    - Keywords only, not full sentences
    - Subtle nudges, not scripts

    Example:
    Question: "Tell me about a time you led a team"

    Copilot Output:
    • Situation: Group project, CS course
    • Task: Lead team of 4, tight deadline
    • Action: Organized weekly sprints, delegated tasks
    • Result: A+ grade, project showcased at expo
    • Highlight: Conflict resolution, time management

    FOCUS AREAS:
    - STAR method structure for behavioral questions
    - Key technical terms and concepts
    - Company values and cultural fit keywords
    - South African employment context
    - Confidence-building reminders
    """
)

# Create the interview copilot instance
interview_copilot = _create_interview_copilot()
