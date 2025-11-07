"""
Test configuration and fixtures for the main Agno application tests.
"""
import os
import pytest
from unittest.mock import Mock, patch

# Ignore test files that reference non-existent 'app' module
def pytest_ignore_collect(path, config):
    """Ignore test files that import from non-existent 'app' module."""
    ignored_files = [
        'test_custom_agents.py',
        'test_hitl.py',
        'test_knowledge.py',
        'test_task_queue.py',
    ]
    if path.basename in ignored_files:
        return True
    return None


@pytest.fixture
def mock_openrouter_api_key():
    """Mock OpenRouter API key for testing."""
    return "sk-or-v1-test-key-12345"


@pytest.fixture
def mock_openai_api_key():
    """Mock OpenAI API key for testing."""
    return "sk-test-openai-key-12345"


@pytest.fixture(autouse=True)
def mock_env_vars(mock_openrouter_api_key):
    """Set up mock environment variables for all tests."""
    with patch.dict(os.environ, {
        "OPENROUTER_API_KEY": mock_openrouter_api_key,
        "OPENAI_API_KEY": "",
    }):
        yield


@pytest.fixture
def mock_openrouter_model():
    """Mock OpenRouter model for testing."""
    mock_model = Mock()
    mock_model.id = "deepseek-chat"
    mock_model.api_key = "sk-or-v1-test-key-12345"
    return mock_model


@pytest.fixture
def mock_agent():
    """Mock Agno agent for testing."""
    mock_agent = Mock()
    mock_agent.name = "Test Agent"
    mock_agent.model = Mock()
    mock_agent.add_history_to_context = True
    mock_agent.markdown = True
    return mock_agent
