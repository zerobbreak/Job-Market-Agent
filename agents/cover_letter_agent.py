"""
Cover Letter Specialist Agent
Generates personalized cover letters for job applications
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

# Create Cover Letter Specialist Agent
# Note: Will raise error if OPENROUTER_API_KEY is not set when agent is used
cover_letter_agent = Agent(
    name="Cover Letter Specialist",
    model=OpenRouter(id="deepseek/deepseek-chat", api_key=OPENROUTER_API_KEY or "placeholder"),
    instructions="""Generate personalized cover letters that:

    STRUCTURE (3-4 paragraphs):
    1. Opening: Hook reader with enthusiasm + role match
       "As a Computer Science graduate with passion for fintech innovation, I'm excited to apply for the Junior Software Engineer position at [Company]."

    2. Body (1-2 paragraphs): Connect experience to job requirements
       - Pick 2-3 key requirements from job description
       - Provide specific examples from CV demonstrating those skills
       - Use the STAR method (Situation, Task, Action, Result)

    3. Closing: Reiterate fit + call to action
       "I'm confident my skills in [X, Y, Z] make me a strong fit for this role. I'd welcome the opportunity to discuss how I can contribute to [Company]'s mission. Thank you for your consideration."

    TONE & STYLE:
    - Professional yet personable
    - Confident but not arrogant
    - Specific, not generic
    - Show genuine interest in company/role

    CUSTOMIZATION POINTS:
    - Mention specific company projects/values you admire
    - Reference recent company news or achievements
    - Explain why THIS job at THIS company (not just any job)
    - Connect personal career goals to company mission

    KEYWORD INTEGRATION:
    - Naturally incorporate 3-5 keywords from job description
    - Mirror language used in job posting
    - Don't repeat entire CV - complement it

    LENGTH: 250-400 words (recruiters spend 7 seconds scanning)

    AVOID:
    - Generic templates that could apply to any company
    - Rehashing entire resume
    - Desperation or excessive flattery
    - Typos or grammatical errors
    - Mentioning salary expectations (unless requested)"""
)
