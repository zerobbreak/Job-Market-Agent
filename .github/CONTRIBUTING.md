# Contributing to Job Market Agent

Thank you for your interest in contributing to Job Market Agent! 🎉 We welcome contributions from the community and are grateful for your support.

## 📋 Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## 📜 Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful, inclusive, and considerate in all interactions.

### Our Standards
- ✅ Be respectful and inclusive
- ✅ Welcome newcomers and help them get started
- ✅ Focus on what is best for the community
- ✅ Show empathy towards other community members
- ❌ No harassment, trolling, or discriminatory language
- ❌ No personal attacks or political arguments

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
- Git
- Basic understanding of web scraping and AI agents
- Familiarity with the project's tech stack (see README.md)

### First Time Contributors
If you're new to open source, check out these resources:
- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)
- [First Contributions](https://github.com/firstcontributions/first-contributions)

Look for issues labeled `good-first-issue` or `help-wanted` to get started!

## 💻 Development Setup

1. **Fork the repository**
   ```bash
   # Click the "Fork" button on GitHub
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR-USERNAME/Job-Market-Agent.git
   cd Job-Market-Agent
   ```

3. **Set up the upstream remote**
   ```bash
   git remote add upstream https://github.com/zerobbreak/Job-Market-Agent.git
   ```

4. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

5. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

6. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

7. **Run tests to verify setup**
   ```bash
   pytest
   ```

## 🤝 How to Contribute

### Types of Contributions
- 🐛 **Bug Fixes**: Fix issues and improve stability
- ✨ **New Features**: Add new functionality
- 📚 **Documentation**: Improve docs, add examples
- 🎨 **Code Quality**: Refactoring, optimization
- ✅ **Tests**: Add or improve test coverage
- 🔧 **DevOps**: CI/CD, Docker, deployment improvements

### Workflow

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**
   - Write clean, readable code
   - Follow the coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run all tests
   pytest
   
   # Run specific test file
   pytest tests/test_specific.py
   
   # Run with coverage
   pytest --cov=. --cov-report=html
   ```

4. **Format your code**
   ```bash
   # Format with Black
   black .
   
   # Sort imports with isort
   isort .
   
   # Lint with flake8
   flake8 .
   
   # Type check with mypy
   mypy main.py utils/ agents/
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill out the PR template completely
   - Link related issues

## 📏 Coding Standards

### Python Style Guide
We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line Length**: Maximum 100 characters (not 79)
- **Formatting**: Use `black` for automatic formatting
- **Import Sorting**: Use `isort` with black-compatible settings
- **Type Hints**: Use type hints for all function signatures
- **Docstrings**: Use Google-style docstrings

### Code Quality Tools
```bash
# Install development tools
pip install black isort flake8 mypy pylint bandit safety

# Run all quality checks
black --check .
isort --check-only .
flake8 .
mypy main.py utils/ agents/
bandit -r .
safety check
```

### Example Code Style
```python
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class JobScraper:
    """Scrapes job listings from various platforms.
    
    This class handles the scraping logic for multiple job boards
    and normalizes the data into a consistent format.
    
    Attributes:
        platform: The job platform to scrape from.
        max_results: Maximum number of results to return.
    """
    
    def __init__(self, platform: str, max_results: int = 100) -> None:
        """Initialize the job scraper.
        
        Args:
            platform: Name of the job platform (e.g., 'linkedin', 'indeed').
            max_results: Maximum number of job listings to scrape.
            
        Raises:
            ValueError: If platform is not supported.
        """
        self.platform = platform
        self.max_results = max_results
        
    def scrape_jobs(
        self, 
        query: str, 
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Scrape job listings based on query and location.
        
        Args:
            query: Search query for job titles or keywords.
            location: Optional location filter.
            
        Returns:
            List of job dictionaries with normalized fields.
            
        Raises:
            ScrapingError: If scraping fails.
        """
        try:
            # Implementation here
            pass
        except Exception as e:
            logger.error(f"Failed to scrape jobs: {e}")
            raise
```

## ✅ Testing Guidelines

### Test Structure
```
tests/
├── unit/           # Unit tests for individual functions
├── integration/    # Integration tests for components
├── e2e/           # End-to-end tests
└── fixtures/      # Test data and fixtures
```

### Writing Tests
- Write tests for all new functionality
- Aim for >80% code coverage
- Use descriptive test names
- Use fixtures for common test data
- Mock external API calls

### Example Test
```python
import pytest
from unittest.mock import Mock, patch
from your_module import JobScraper


class TestJobScraper:
    """Test suite for JobScraper class."""
    
    @pytest.fixture
    def scraper(self):
        """Create a JobScraper instance for testing."""
        return JobScraper(platform="linkedin", max_results=10)
    
    def test_scrape_jobs_success(self, scraper):
        """Test successful job scraping."""
        with patch('your_module.requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"jobs": []}
            results = scraper.scrape_jobs("python developer")
            assert isinstance(results, list)
    
    def test_scrape_jobs_invalid_platform(self):
        """Test that invalid platform raises ValueError."""
        with pytest.raises(ValueError):
            JobScraper(platform="invalid_platform")
```

## 📝 Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes
- `build`: Build system changes

### Examples
```bash
feat(scraper): add support for Indeed job scraping

- Implement Indeed scraper class
- Add rate limiting for API calls
- Update documentation

Closes #123

---

fix(auth): resolve token expiration issue

The authentication token was not being refreshed properly,
causing requests to fail after 1 hour.

Fixes #456

---

docs(readme): update installation instructions

- Add Docker setup steps
- Clarify API key requirements
- Fix broken links
```

### Rules
- Use present tense ("add feature" not "added feature")
- Use imperative mood ("move cursor to..." not "moves cursor to...")
- First line should be ≤50 characters
- Body should wrap at 72 characters
- Reference issues and PRs in footer

## 🔄 Pull Request Process

### Before Submitting
- ✅ All tests pass locally
- ✅ Code is formatted with `black` and `isort`
- ✅ No linting errors from `flake8`
- ✅ Type checking passes with `mypy`
- ✅ Documentation is updated
- ✅ CHANGELOG.md is updated (if applicable)

### PR Requirements
1. **Fill out the PR template completely**
2. **Link related issues** using keywords (Fixes #123, Closes #456)
3. **Provide clear description** of changes and motivation
4. **Include tests** for new functionality
5. **Update documentation** as needed
6. **Ensure CI passes** - all automated checks must pass
7. **Request review** from maintainers

### Review Process
- Maintainers will review your PR within 3-5 business days
- Address review comments promptly
- Keep discussions focused and professional
- Be open to feedback and suggestions
- Once approved, a maintainer will merge your PR

### After Merge
- Delete your feature branch
- Update your local repository
- Celebrate your contribution! 🎉

## 🐛 Reporting Bugs

### Before Reporting
1. Check existing issues to avoid duplicates
2. Verify you're using the latest version
3. Collect relevant information (OS, Python version, error logs)

### Bug Report Template
Use the bug report template when creating an issue. Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Error logs and screenshots
- Possible solutions (if any)

## 💡 Suggesting Features

### Before Suggesting
1. Check existing issues and discussions
2. Ensure it aligns with project goals
3. Consider if it benefits the broader community

### Feature Request Template
Use the feature request template. Include:
- Clear description of the feature
- Problem it solves
- Proposed solution
- Use cases
- Implementation suggestions (optional)

## 🏆 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in relevant documentation

## 📞 Getting Help

- 💬 **Discussions**: Use GitHub Discussions for questions
- 📧 **Email**: Contact maintainers for private matters
- 📚 **Documentation**: Check README.md and docs/
- 🐛 **Issues**: Report bugs via GitHub Issues

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

Thank you for contributing to Job Market Agent! Your efforts help make this project better for everyone. 🙏
