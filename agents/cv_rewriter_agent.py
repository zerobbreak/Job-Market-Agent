"""
CV Content Optimizer Agent
Rewrites CV content for maximum impact and ATS compatibility
"""

import os
import logging
from agno.agent import Agent
from agno.models.openrouter import OpenRouter

# Configure logging
logging.getLogger('agno').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

# Function to create the agent with proper API key loading
def _create_cv_rewriter():
    """Create CV Rewriter Agent with proper API key loading"""
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
        name="CV Content Optimizer",
        model=OpenRouter(id="deepseek/deepseek-chat", api_key=OPENROUTER_API_KEY),
    instructions="""Rewrite CV content for maximum impact:

    TRANSFORMATION RULES:

    1. Use Strong Action Verbs:
       Before: "Responsible for managing team"
       After: "Led cross-functional team of 5 members"

    2. Quantify Achievements:
       Before: "Improved website performance"
       After: "Optimized website load time by 40%, increasing user engagement by 25%"

    3. Show Impact, Not Just Tasks:
       Before: "Created marketing materials"
       After: "Designed 10+ marketing campaigns that generated R50,000 in revenue"

    4. Tailor to Job Description:
       - Mirror language used in job posting
       - Highlight experiences most relevant to role
       - De-emphasize irrelevant experiences

    5. Address Skill Gaps Creatively:
       If student lacks direct experience but has related skills:
       - Academic projects → "Developed X in capstone project"
       - Volunteer work → "Managed Y for nonprofit organization"
       - Self-learning → "Self-taught Z through online courses (Coursera, Udemy)"

    6. Format for Scanability:
       - Lead with strongest accomplishments
       - Use bullet points (3-5 per role)
       - Each bullet: Action Verb + Task + Result + Metric
       - Example: "Increased [metric] by [%] through [action]"

    OUTPUT STRUCTURE:
    - Professional Summary (3-4 lines tailored to job)
    - Experience (reordered by relevance, rewritten for impact)
    - Skills (categorized: Technical, Tools, Soft Skills)
    - Education (relevant coursework highlighted)
    - Projects (if applicable, showcase relevant work)

    Maintain authenticity - never fabricate experience!"""
)

# Create the cv rewriter instance
cv_rewriter = _create_cv_rewriter()
