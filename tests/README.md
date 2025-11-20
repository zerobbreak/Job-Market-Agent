# Job Market AI Agent Tests

This directory contains comprehensive test suites for all AI agents in the Job Market AI system.

## Test Structure

### Student-Facing Agents
- `test_profile_agent.py` - Tests for Career Intelligence Analyst
- `test_job_matcher_agent.py` - Tests for Opportunity Discovery Engine
- `test_ats_optimizer_agent.py` - Tests for ATS Optimization Specialist
- `test_cv_rewriter_agent.py` - Tests for CV Content Strategist
- `test_cover_letter_agent.py` - Tests for Cover Letter Storyteller
- `test_interview_prep_agent.py` - Tests for Interview Intelligence Coach

### Test Infrastructure
- `conftest.py` - Shared fixtures and test configuration
- `__init__.py` - Makes tests directory a Python package

## Running Tests

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test File
```bash
python run_tests.py test_profile_agent.py
python run_tests.py profile_agent  # Also works (auto-completes)
```

### List Available Tests
```bash
python run_tests.py --list
```

### Using pytest Directly
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_profile_agent.py

# Run with coverage
pytest tests/ --cov=agents --cov-report=html

# Run tests matching pattern
pytest tests/ -k "profile"
```

## Test Coverage

The test suite covers:

### Agent Initialization
- Proper agent naming and configuration
- Model and instruction setup
- Tool integration (where applicable)

### Instruction Validation
- Comprehensive instruction content verification
- South African context inclusion
- Required sections and methodologies

### Functional Testing
- Mock-based agent response testing
- Input/output validation
- Error handling scenarios

### Integration Testing
- Cross-agent compatibility
- Data flow validation
- End-to-end workflow testing

## Mock Data

The test suite uses realistic mock data including:

- Sample student profiles with SA context
- Job descriptions with local requirements
- CV content with relevant experience
- Interview scenarios and responses

## Dependencies

Tests require:
- pytest (included in requirements.txt)
- All agent dependencies (automatically mocked where needed)

## Test Philosophy

1. **Isolation**: Each test is independent and doesn't rely on external services
2. **Realism**: Mock data reflects actual usage patterns
3. **Coverage**: Tests validate both success and edge cases
4. **Maintainability**: Clear test structure and documentation

## Adding New Tests

When adding tests for new agents:

1. Create `test_<agent_name>_agent.py`
2. Follow the established pattern:
   - Test agent initialization
   - Validate instructions contain key sections
   - Test functional behavior with mocks
   - Verify output format compliance
3. Add agent to this README
4. Update `run_tests.py` if needed

## Continuous Integration

Tests are designed to run in CI/CD environments:
- No external dependencies beyond what's in requirements.txt
- Fast execution (under 30 seconds for full suite)
- Clear pass/fail indicators
- Detailed error reporting
