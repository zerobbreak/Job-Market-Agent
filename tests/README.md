# Agno Application Tests

This directory contains tests for the main Agno application functionality.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Test configuration and fixtures
├── test_main.py             # Tests for main.py functionality
├── test_models.py           # Tests for OpenRouter model configuration
├── run_tests.py             # Simple test runner script
├── requirements.txt         # Test dependencies
└── README.md               # This file
```

## Running Tests

### Option 1: Using the test runner script
```bash
cd tests
python run_tests.py
```

### Option 2: Using pytest directly
```bash
# From the project root
pytest tests/ -v

# With coverage
pytest tests/ --cov=main --cov-report=html
```

### Option 3: Running specific test files
```bash
pytest tests/test_main.py -v
pytest tests/test_models.py -v
```

## Test Coverage

The tests cover:

1. **Configuration Testing** (`test_main.py`):
   - Model dictionary structure and content
   - Default model selection
   - OpenRouter model format validation
   - Command-line interface functionality

2. **Model Testing** (`test_models.py`):
   - OpenRouter model configuration
   - Provider-specific model validation
   - API key configuration
   - Model initialization

## Fixtures

The `conftest.py` file provides:
- Mock API keys for testing
- Mock OpenRouter model instances
- Mock Agno agent instances
- Environment variable mocking

## Dependencies

Install test dependencies:
```bash
pip install -r tests/requirements.txt
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines and provide fast feedback on:
- Code changes that break existing functionality
- Model configuration issues
- API integration problems
