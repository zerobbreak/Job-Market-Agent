# .github Directory

This directory contains GitHub-specific configuration files, templates, and workflows for the Job Market Agent project.

## 📁 Directory Structure

```
.github/
├── ISSUE_TEMPLATE/          # Issue templates
│   ├── bug_report.md        # Bug report template
│   ├── feature_request.md   # Feature request template
│   └── config.yml           # Issue template configuration
├── workflows/               # GitHub Actions workflows
│   ├── ci-cd.yml           # Main CI/CD pipeline
│   ├── stale.yml           # Stale issue/PR management
│   ├── greetings.yml       # Welcome new contributors
│   └── auto-assign.yml     # Auto-assign issues/PRs
├── CONTRIBUTING.md          # Contribution guidelines
├── SECURITY.md             # Security policy
├── PULL_REQUEST_TEMPLATE.md # PR template
├── CODEOWNERS              # Code ownership rules
├── FUNDING.yml             # Funding/sponsorship info
├── dependabot.yml          # Dependabot configuration
└── labeler.yml             # Auto-labeling rules
```

## 📋 Issue Templates

### Bug Report (`ISSUE_TEMPLATE/bug_report.md`)
Template for reporting bugs with sections for:
- Bug description
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Error logs
- Screenshots

### Feature Request (`ISSUE_TEMPLATE/feature_request.md`)
Template for suggesting new features with sections for:
- Feature description
- Problem statement
- Proposed solution
- Use cases
- Impact analysis
- Implementation suggestions

### Config (`ISSUE_TEMPLATE/config.yml`)
Configures issue creation with links to:
- Q&A discussions
- Ideas & suggestions
- Documentation
- Security vulnerability reporting

## 🔄 Workflows

### CI/CD Pipeline (`workflows/ci-cd.yml`)
Comprehensive CI/CD workflow with:

**Quality Checks:**
- Code formatting (Black, isort)
- Linting (flake8, pylint)
- Type checking (mypy)
- Security scanning (Bandit, Safety)

**Testing:**
- Multi-version Python testing (3.10, 3.11, 3.12)
- Code coverage reporting
- Codecov integration
- Coverage comments on PRs

**Security:**
- CodeQL analysis
- Docker image scanning (Trivy)
- Dependency review
- SARIF report uploads

**Docker:**
- Build and test Docker images
- Push to Docker Hub (on release)
- Vulnerability scanning

**Release:**
- Automated changelog generation
- GitHub releases
- Docker image tagging

**Triggers:**
- Push to main/master/develop
- Pull requests
- Manual dispatch
- Weekly schedule

### Stale Bot (`workflows/stale.yml`)
Automatically manages inactive issues and PRs:
- **Issues:** Marked stale after 60 days, closed after 7 more days
- **PRs:** Marked stale after 30 days, closed after 14 more days
- **Exemptions:** Critical, security, pinned items
- **Actions:** Friendly messages, automatic labeling

### Greetings (`workflows/greetings.yml`)
Welcomes first-time contributors with:
- Friendly welcome message
- Links to helpful resources
- Next steps guidance
- Community guidelines

### Auto-assign (`workflows/auto-assign.yml`)
Automatically assigns new issues and PRs to maintainers for better tracking.

### Auto-labeler (`labeler.yml`)
Automatically labels PRs based on changed files:
- `documentation` - Markdown and docs changes
- `python` - Python code changes
- `tests` - Test file changes
- `ci-cd` - CI/CD and Docker changes
- `dependencies` - Dependency updates
- `configuration` - Config file changes
- And more...

## 📚 Documentation

### Contributing Guide (`CONTRIBUTING.md`)
Comprehensive guide covering:
- Code of conduct
- Development setup
- Contribution workflow
- Coding standards
- Testing guidelines
- Commit message conventions
- Pull request process

### Security Policy (`SECURITY.md`)
Security guidelines including:
- Vulnerability reporting process
- Supported versions
- Security best practices
- Security scanning tools
- Security checklist for PRs

### Pull Request Template (`PULL_REQUEST_TEMPLATE.md`)
Detailed PR template with:
- Description and related issues
- Type of change checklist
- Testing information
- Code quality checklist
- Documentation updates
- Security considerations

## 🔧 Configuration Files

### CODEOWNERS
Defines code ownership for automatic review requests:
- Core application files
- Utilities and agents
- Configuration files
- Docker and deployment
- CI/CD workflows
- Documentation
- Tests and dependencies

### Dependabot (`dependabot.yml`)
Automated dependency updates for:
- **Python packages** - Weekly updates, grouped by type
- **GitHub Actions** - Weekly updates, grouped together
- **Docker images** - Weekly updates
- **Features:**
  - Automatic PR creation
  - Semantic commit messages
  - Automatic labeling
  - Version grouping
  - Major version ignoring for critical deps

### Funding (`FUNDING.yml`)
Template for accepting sponsorships through:
- GitHub Sponsors
- Patreon
- Open Collective
- Ko-fi
- Buy Me a Coffee
- And more...

## 🚀 Getting Started

### For Contributors

1. **Read the Contributing Guide**
   ```bash
   cat .github/CONTRIBUTING.md
   ```

2. **Use Issue Templates**
   - Click "New Issue" on GitHub
   - Select appropriate template
   - Fill out all sections

3. **Create Pull Requests**
   - Fork the repository
   - Create a feature branch
   - Make your changes
   - Fill out the PR template
   - Wait for CI checks to pass

### For Maintainers

1. **Review Dependabot PRs**
   - Check weekly dependency updates
   - Review and merge safe updates
   - Test major version updates

2. **Monitor CI/CD**
   - Check workflow runs
   - Review security reports
   - Monitor code coverage

3. **Manage Issues/PRs**
   - Review auto-assigned items
   - Respond to stale notifications
   - Welcome new contributors

## 🔒 Security

### Automated Security Scanning
- **Bandit** - Python security linter
- **Safety** - Dependency vulnerability scanner
- **CodeQL** - Semantic code analysis
- **Trivy** - Docker image scanning
- **Dependabot** - Dependency security alerts

### Security Reporting
- Use GitHub Security Advisories
- Follow responsible disclosure
- Check SECURITY.md for details

## 📊 Metrics & Monitoring

### Code Quality
- Automated linting and formatting checks
- Type checking with mypy
- Code complexity analysis

### Test Coverage
- Multi-version Python testing
- Coverage reports on PRs
- Codecov integration
- Minimum coverage thresholds

### Security
- Vulnerability scanning
- SARIF reports in Security tab
- Dependency review on PRs

## 🎯 Best Practices

### For Issues
- Use appropriate templates
- Provide detailed information
- Include error logs and screenshots
- Search for duplicates first

### For Pull Requests
- Fill out the template completely
- Link related issues
- Ensure CI passes
- Update documentation
- Add tests for new features

### For Commits
- Follow conventional commits
- Write clear commit messages
- Keep commits focused
- Reference issues when applicable

## 🔄 Workflow Permissions

All workflows use minimal required permissions:
- `contents: read/write` - For code access and releases
- `pull-requests: write` - For PR comments and labels
- `issues: write` - For issue management
- `security-events: write` - For security scanning

## 📞 Support

- **Issues:** Use GitHub Issues with templates
- **Discussions:** Use GitHub Discussions for Q&A
- **Security:** See SECURITY.md for vulnerability reporting
- **Contributing:** See CONTRIBUTING.md for guidelines

## 📝 Maintenance

### Regular Tasks
- Review and merge Dependabot PRs
- Monitor CI/CD workflow runs
- Update workflow versions
- Review security reports
- Manage stale issues/PRs

### Quarterly Reviews
- Update Python versions in CI
- Review and update dependencies
- Update documentation
- Review security policies

---

**Last Updated:** 2025-11-20

For questions or suggestions about these configurations, please open an issue or discussion.
