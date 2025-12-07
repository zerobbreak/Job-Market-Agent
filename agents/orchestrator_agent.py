"""
Orchestrator Agent (The Manager)
Central intelligence that delegates tasks to specialist agents.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from agno.agent import Agent
from agno.models.google import Gemini

# Configure logging
logging.getLogger('google.genai').setLevel(logging.WARNING)
logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('agno').setLevel(logging.WARNING)

# Suppress API key confirmation messages
gemini_key_backup = os.environ.get('GEMINI_API_KEY')
if 'GEMINI_API_KEY' in os.environ:
    del os.environ['GEMINI_API_KEY']

from utils.memory_store import memory

# Lazy import to avoid circular dependency
def _get_agents():
    """Lazy load agents to avoid circular imports"""
    from .profile_agent import profile_builder
    from .job_intelligence_agent import job_intelligence
    from .application_writer_agent import application_writer
    from .interview_prep_agent import interview_prep_agent
    return {
        'profile_builder': profile_builder,
        'job_intelligence': job_intelligence,
        'application_writer': application_writer,
        'interview_prep_agent': interview_prep_agent
    }



def find_jobs(query: str, location: str = "South Africa") -> str:
    """
    Find job opportunities and provide market intelligence.
    Delegates to the Job Intelligence Agent.
    """
    agents = _get_agents()
    # Check memory for similar jobs first
    similar_jobs = memory.find_similar_jobs(f"{query} in {location}")
    memory_context = ""
    if similar_jobs:
        memory_context = "\n\n[MEMORY] Found similar jobs in history:\n"
        for job in similar_jobs:
            memory_context += f"- {job['metadata']['title']} at {job['metadata']['company']} (Source: {job['metadata']['source']})\n"

    return agents['job_intelligence'].run(f"Find jobs matching: {query} in {location}. {memory_context}").content

def optimize_cv(cv_text: str, job_description: str) -> str:
    """
    Optimize a CV for a specific job and ensure ATS compatibility.
    Delegates to the Application Writer Agent.
    """
    agents = _get_agents()
    return agents['application_writer'].run(f"Optimize this CV for the following job:\n\nCV:\n{cv_text}\n\nJob:\n{job_description}").content

def write_cover_letter(cv_text: str, job_description: str) -> str:
    """
    Write a personalized cover letter for a job application.
    Delegates to the Application Writer Agent.
    """
    agents = _get_agents()
    return agents['application_writer'].run(f"Write a cover letter for this job based on the CV:\n\nCV:\n{cv_text}\n\nJob:\n{job_description}").content

def create_application_package(cv_text: str, job_description: str) -> str:
    """
    Create a complete application package (optimized CV + cover letter).
    Delegates to the Application Writer Agent.
    """
    agents = _get_agents()
    return agents['application_writer'].run(f"Create a complete application package (optimized CV + cover letter) for:\n\nCV:\n{cv_text}\n\nJob:\n{job_description}").content

def prepare_for_interview(job_description: str) -> str:
    """
    Generate interview preparation questions and tips.
    Delegates to the Interview Prep Agent.
    """
    agents = _get_agents()
    return agents['interview_prep_agent'].run(f"Prepare me for an interview for this job:\n{job_description}").content

def get_market_insights(query: str) -> str:
    """
    Get market trends, salary predictions, and career insights.
    Delegates to the Job Intelligence Agent.
    """
    agents = _get_agents()
    return agents['job_intelligence'].run(f"Provide market intelligence for: {query}").content


# Create the Orchestrator Agent
orchestrator_agent = Agent(
    name="Career Concierge",
    model=Gemini(id="gemini-1.5-pro"),
    instructions="""You are the Career Concierge, a personal career manager for the user.
    Your goal is to help the user navigate their career journey by coordinating a team of specialist agents.

    YOUR TEAM:
    1. Job Intelligence: Finds jobs, matches candidates, provides market insights and salary predictions
    2. Application Writer: Optimizes CVs for ATS, writes cover letters, creates complete application packages
    3. Interview Coach: Prepares users for interviews with questions and strategies
    4. Profile Builder: Analyzes user background and career goals

    MEMORY & CONTEXT:
    - You have access to a long-term memory of past jobs and user preferences.
    - Use this context to personalize your recommendations.
    - If the user has rejected similar jobs in the past, warn them or filter them out.

    HOW TO OPERATE:
    - Receive a request from the user (e.g., "Find me a Python job").
    - Break it down into steps.
    - CALL THE APPROPRIATE TOOLS to get the work done.
    - Synthesize the results into a clear, helpful response.

    EXAMPLE WORKFLOWS:
    
    User: "Find me a Python job in Cape Town"
    You: Call `find_jobs("Python Developer", "Cape Town")`
    
    User: "I want to apply to this Google job. Here is the JD..."
    You:
    1. Call `create_application_package(cv, job_description)` to get optimized CV + cover letter
    2. Present the package to the user
    
    User: "What's the salary range for Data Scientists in Johannesburg?"
    You: Call `get_market_insights("Data Scientist salary Johannesburg")`

    Be proactive, encouraging, and strategic.
    """,
    tools=[
        find_jobs,
        optimize_cv,
        write_cover_letter,
        create_application_package,
        prepare_for_interview,
        get_market_insights
    ],
    markdown=True
)

# Restore GEMINI_API_KEY if it was set
if gemini_key_backup:
    os.environ['GEMINI_API_KEY'] = gemini_key_backup


# Restore GEMINI_API_KEY if it was set
if gemini_key_backup:
    os.environ['GEMINI_API_KEY'] = gemini_key_backup
