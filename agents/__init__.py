"""
Complete CareerBoost AI Agent Suite
Production-ready agents with enhanced instructions, KB integration, and SA customizations
"""

from .profile_agent import profile_builder
from .job_matcher_agent import job_matcher
from .ats_optimizer_agent import ats_optimizer
from .cv_rewriter_agent import cv_rewriter
from .cover_letter_agent import cover_letter_agent
from .interview_prep_agent import interview_prep_agent
from .resume_screening_agent import resume_screening_agent
from .candidate_ranking_agent import candidate_ranking_agent
from .candidate_communication_agent import candidate_communication_agent
from .interview_assistant_agent import interview_assistant_agent
from .hiring_analytics_agent import hiring_analytics_agent
# ML agents excluded due to missing dependencies (spacy, etc.)
# from .ml_resume_screening_agent import ml_resume_screening_agent
# from .ml_job_matcher_agent import ml_job_matcher_agent
# from .ml_candidate_ranking_agent import ml_candidate_ranking_agent
# from .ml_predictive_analytics_agent import ml_predictive_analytics_agent

# ============================================================================
# HELPER FUNCTIONS FOR AGENT INTEGRATION
# ============================================================================

def get_agent_by_name(agent_name: str):
    """
    Get agent instance by name

    Args:
        agent_name: Name of the agent to retrieve

    Returns:
        Agent instance
    """
    agents = {
        'profile_builder': profile_builder,
        'job_matcher': job_matcher,
        'ats_optimizer': ats_optimizer,
        'cv_rewriter': cv_rewriter,
        'cover_letter_agent': cover_letter_agent,
        'interview_prep_agent': interview_prep_agent,
        'resume_screening_agent': resume_screening_agent,
        'candidate_ranking_agent': candidate_ranking_agent,
        'candidate_communication_agent': candidate_communication_agent,
        'interview_assistant_agent': interview_assistant_agent,
        'hiring_analytics_agent': hiring_analytics_agent,
        'ml_resume_screening_agent': ml_resume_screening_agent,
        'ml_job_matcher_agent': ml_job_matcher_agent,
        'ml_candidate_ranking_agent': ml_candidate_ranking_agent,
        'ml_predictive_analytics_agent': ml_predictive_analytics_agent
    }

    return agents.get(agent_name)

def get_all_agents():
    """
    Get all available agents

    Returns:
        Dictionary of agent name -> agent instance
    """
    return {
        # Student-facing agents
        'profile_builder': profile_builder,
        'job_matcher': job_matcher,
        'ats_optimizer': ats_optimizer,
        'cv_rewriter': cv_rewriter,
        'cover_letter_agent': cover_letter_agent,
        'interview_prep_agent': interview_prep_agent,

        # Recruiter-facing agents
        'resume_screening_agent': resume_screening_agent,
        'candidate_ranking_agent': candidate_ranking_agent,
        'candidate_communication_agent': candidate_communication_agent,
        'interview_assistant_agent': interview_assistant_agent,
        'hiring_analytics_agent': hiring_analytics_agent

        # ML agents excluded due to missing dependencies
    }

def get_student_agents():
    """Get student-facing agents only"""
    return {
        'profile_builder': profile_builder,
        'job_matcher': job_matcher,
        'ats_optimizer': ats_optimizer,
        'cv_rewriter': cv_rewriter,
        'cover_letter_agent': cover_letter_agent,
        'interview_prep_agent': interview_prep_agent
    }

def get_recruiter_agents():
    """Get recruiter-facing agents only"""
    return {
        'resume_screening_agent': resume_screening_agent,
        'candidate_ranking_agent': candidate_ranking_agent,
        'candidate_communication_agent': candidate_communication_agent,
        'interview_assistant_agent': interview_assistant_agent,
        'hiring_analytics_agent': hiring_analytics_agent
    }

__all__ = [
    # Student-facing agents (6)
    'profile_builder',
    'job_matcher',
    'ats_optimizer',
    'cv_rewriter',
    'cover_letter_agent',
    'interview_prep_agent',

    # Recruiter-facing agents (5)
    'resume_screening_agent',
    'candidate_ranking_agent',
    'candidate_communication_agent',
    'interview_assistant_agent',
    'hiring_analytics_agent',

    # Helper functions
    'get_agent_by_name',
    'get_all_agents',
    'get_student_agents',
    'get_recruiter_agents'

    # ML-enhanced agents
    'ml_resume_screening_agent',
    'ml_job_matcher_agent',
    'ml_candidate_ranking_agent',
    'ml_predictive_analytics_agent',
]

