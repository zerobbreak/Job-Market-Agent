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

# Get OpenRouter API key - required for agent functionality
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    # Allow import for testing, but will fail when agent is actually used
    OPENROUTER_API_KEY = None

# Create Interview Copilot Agent
# Note: Will raise error if OPENROUTER_API_KEY is not set when agent is used
interview_copilot = Agent(
    name="Interview Assistant",
    model=OpenRouter(id="deepseek/deepseek-chat", api_key=OPENROUTER_API_KEY or "placeholder"),
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
