"""
Complete CareerBoost AI Agent Suite
Consolidated architecture with 4 core specialist agents + Orchestrator
"""

from .profile_agent import profile_builder
from .job_intelligence_agent import job_intelligence
from .application_writer_agent import application_writer
from .interview_prep_agent import interview_prep_agent


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
        'job_intelligence': job_intelligence,
        'application_writer': application_writer,
        'interview_prep_agent': interview_prep_agent,

    }

    return agents.get(agent_name)

def get_all_agents():
    """
    Get all available agents

    Returns:
        Dictionary of agent name -> agent instance
    """
    return {
        'profile_builder': profile_builder,
        'job_intelligence': job_intelligence,
        'application_writer': application_writer,
        'interview_prep_agent': interview_prep_agent,

    }

def get_core_agents():
    """Get core specialist agents (excluding orchestrator)"""
    return {
        'profile_builder': profile_builder,
        'job_intelligence': job_intelligence,
        'application_writer': application_writer,
        'interview_prep_agent': interview_prep_agent
    }


__all__ = [
    # Core specialist agents (4)
    'profile_builder',
    'job_intelligence',
    'application_writer',
    'interview_prep_agent',
    
    # Orchestrator


    # Helper functions
    'get_agent_by_name',
    'get_all_agents',
    'get_core_agents'
]