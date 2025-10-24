"""
ATS Optimizer Agent
Optimizes resumes for Applicant Tracking Systems (ATS)
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

# Create ATS Optimization Specialist
ats_optimizer = Agent(
    name="ATS Optimization Specialist",
    model=Gemini(id="gemini-2.0-flash"),
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

# Restore GEMINI_API_KEY if it was set
if gemini_key_backup:
    os.environ['GEMINI_API_KEY'] = gemini_key_backup
