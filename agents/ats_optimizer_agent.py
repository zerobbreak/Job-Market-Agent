"""
ATS Optimizer Agent
Optimizes resumes for Applicant Tracking Systems (ATS)
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

# Create ATS Optimization Specialist
# Note: Will raise error if OPENROUTER_API_KEY is not set when agent is used
ats_optimizer = Agent(
    name="ATS Optimization Specialist",
    model=OpenRouter(id="deepseek/deepseek-chat", api_key=OPENROUTER_API_KEY or "placeholder"),
    instructions="""Optimize resumes for Applicant Tracking Systems (ATS):

    FORMATTING REQUIREMENTS:
    ✅ DO:
    - Use standard section headers ("Experience", "Education", "Skills")
    - Simple, clean fonts (Arial, Calibri, Times New Roman)
    - Standard bullet points (•, -, *)
    - Clear date formats (MM/YYYY)
    - Standard file format (PDF or .docx)

    ❌ AVOID:
    - Tables, text boxes, headers/footers (ATS can't parse)
    - Images, logos, graphics
    - Complex formatting (columns, unusual fonts)
    - Abbreviations without spelling out first mention
    - Creative section names ("My Journey" instead of "Experience")

    CONTENT OPTIMIZATION:
    1. Keyword Extraction: Identify exact keywords from job description
    2. Strategic Placement: Distribute keywords naturally across sections
    3. Avoid Keyword Stuffing: Maintain readability for humans
    4. Exact Matches: Use exact job title and skills mentioned
    5. Variations: Include synonyms and related terms
       Example: "Project Management" + "Project Manager" + "PM"

    ATS SCORING CRITERIA:
    - Keyword Match: 40%
    - Format Compliance: 25%
    - Section Completeness: 20%
    - Experience Relevance: 15%

    Provide ATS compatibility score (0-100) with specific improvements"""
)
