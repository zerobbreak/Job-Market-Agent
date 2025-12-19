"""
Test configuration and shared fixtures for Job Market AI agents
"""

import pytest
import os
from unittest.mock import Mock, patch
from typing import Dict, Any

# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test_key',
        'GOOGLE_API_KEY': 'test_key'
    }):
        yield

@pytest.fixture
def sample_student_profile():
    """Sample student profile data for testing"""
    return {
        "name": "John Doe",
        "education": {
            "degree": "Bachelor of Science in Computer Science",
            "institution": "University of Johannesburg",
            "graduation_year": 2024,
            "gpa": 3.8
        },
        "experience": [
            {
                "role": "Software Development Intern",
                "company": "TechCorp",
                "duration": "6 months",
                "skills": ["Python", "JavaScript", "React"]
            }
        ],
        "skills": {
            "technical": ["Python", "JavaScript", "SQL", "Git"],
            "soft": ["Communication", "Teamwork", "Problem Solving"]
        },
        "career_goals": {
            "short_term": "Junior Software Developer",
            "long_term": "Senior Software Engineer",
            "preferred_industries": ["Technology", "Finance"]
        }
    }

@pytest.fixture
def sample_job_description():
    """Sample job description for testing"""
    return {
        "title": "Junior Software Developer",
        "company": "Tech Solutions Inc",
        "location": "Johannesburg, South Africa",
        "requirements": {
            "experience": "0-2 years",
            "skills": ["Python", "JavaScript", "SQL", "Git"],
            "education": "Bachelor's degree in Computer Science or related field"
        },
        "salary_range": "R15,000 - R25,000 per month",
        "description": "We are looking for a passionate junior developer to join our team..."
    }

@pytest.fixture
def sample_cv_content():
    """Sample CV content for testing"""
    return """
    JOHN DOE
    Software Developer

    EDUCATION
    Bachelor of Science in Computer Science
    University of Johannesburg, 2024
    GPA: 3.8/4.0

    EXPERIENCE
    Software Development Intern
    TechCorp, Johannesburg
    June 2023 - December 2023
    - Developed web applications using Python and JavaScript
    - Collaborated with cross-functional teams
    - Implemented database solutions using SQL

    SKILLS
    - Programming: Python, JavaScript, Java
    - Web Development: React, HTML, CSS
    - Databases: MySQL, PostgreSQL
    - Tools: Git, Docker, AWS

    PROJECTS
    E-commerce Website
    - Built full-stack web application
    - Technologies: React, Node.js, MongoDB
    """

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response"""
    def _mock_response(content: str = "Mock response"):
        mock_response = Mock()
        mock_response.text = content
        return mock_response

    return _mock_response

@pytest.fixture
def mock_agent_run():
    """Mock agent run method"""
    def _mock_run(message: str, **kwargs):
        return f"Mock response to: {message}"

    return _mock_run

@pytest.fixture
def mock_file_tools():
    """Mock file tools for testing"""
    mock_tools = Mock()
    mock_tools.read_file.return_value = "Mock file content"
    mock_tools.write_file.return_value = True
    return mock_tools
