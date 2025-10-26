# Job Market AI Analyzer

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![CI/CD](https://img.shields.io/badge/CI/CD-GitHub%20Actions-orange.svg)](https://github.com/features/actions)

Advanced AI-powered job matching for students and professionals with intelligent CV analysis, personalized job recommendations, and automated cover letter generation.

## ✨ Key Features

### 🤖 AI-Powered Intelligence
- **Smart CV Analysis** - Extracts skills, experience, and career goals from your CV using advanced AI
- **Intelligent Job Search** - Searches for jobs based on your extracted profile, not generic terms
- **Personalized Matching** - Multi-dimensional scoring with semantic skill analysis
- **Automated Cover Letters** - Generates tailored cover letters for matched positions

### 🚀 Performance & Reliability
- **Advanced Caching** - TTLCache with metrics, 24h job data caching, automatic expiration
- **Progress Tracking** - Real-time progress bars and performance monitoring
- **Robust Error Handling** - Retry logic, graceful degradation, input validation
- **Security First** - Input sanitization, file validation, safe API handling

### 🎯 Smart Features
- **Multi-Site Scraping** - Indeed, LinkedIn, Google, Glassdoor, ZipRecruiter, Naukri, BDJobs
- **Cost Optimization** - Intelligent caching reduces API costs by 70-90%
- **Batch Processing** - Efficient handling of large job datasets
- **Configurable** - Environment-based settings for all parameters

## ✨ Features

### Core AI Capabilities
- **Advanced CV Analysis**: Uses Google Gemini to extract structured profiles from PDF CVs
- **Intelligent Job Matching**: Multi-dimensional scoring algorithm with semantic skill matching
- **CV Tailoring Engine**: Automatically generates job-specific CV versions optimized for ATS
- **Cover Letter Generation**: AI-powered personalized cover letters for specific roles
- **Interview Preparation**: Realistic interview question prediction and practice scenarios
- **Mock Interview Simulator**: Interactive interview practice with AI interviewer and copilot

### Job Discovery & Analysis
- **Multi-Site Job Scraping**: Scrapes jobs from PNet, CareerJunction, and Indeed South Africa
- **Vector Database Storage**: ChromaDB for efficient similarity search and caching
- **Real-time Job Discovery**: Integrated scraping with intelligent deduplication
- **South African Localization**: Custom job recommendations considering transport, culture, and market conditions

### Specialized AI Agents
- **Profile Builder**: Extracts education, experience, skills, and career aspirations
- **Job Matcher**: Performs detailed multi-dimensional job matching with embeddings
- **ATS Optimizer**: Analyzes and improves CV compatibility with Applicant Tracking Systems
- **CV Rewriter**: Tailors CV content for specific job requirements
- **Cover Letter Agent**: Generates personalized, role-specific cover letters
- **Interview Prep Agent**: Predicts likely interview questions across multiple categories
- **Interview Copilot**: Provides real-time hints during mock interviews

### Ethical & Safe AI
- **Ethical Guidelines Framework**: Comprehensive framework ensuring responsible AI use
- **Bias Mitigation**: South African context-aware recommendations
- **Transparency**: Clear disclosure of AI assistance and limitations
- **User Consent Management**: Ethical handling of personal data and career information

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google AI API Key ([Get one here](https://makersuite.google.com/app/apikey))
- Your CV in PDF format

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/[YOUR_USERNAME]/job-market-analyzer.git
cd job-market-analyzer
```

2. **Create virtual environment:**
```bash
python -m venv venv
```

3. **Activate virtual environment:**
```bash
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
python -m playwright install  # Install browser for scraping
```

5. **Add your CV:**
```bash
# Replace CV_PLACEHOLDER.txt with your actual CV in PDF format
# Rename your CV file to "CV.pdf" in the project root
cp /path/to/your/cv.pdf CV.pdf
```

6. **Configure environment:**
```bash
cp env.example .env
# Edit .env with your Google API key
```

7. **Run the analyzer:**
```bash
python main.py
```

### Basic Usage

```bash
# Analyze CV and find jobs
python main.py

# Use specific CV and goals
python main.py --cv-path my_cv.pdf --goals "I want to become a data scientist"

# Verbose output with progress tracking
python main.py --verbose

# Show version
python main.py --version

# Start web server with health checks
python main.py --web-server --port 8000

# GDPR/POPIA Compliance (Platform Mode)
python main.py --platform --export-data <student_id>    # Export all student data
python main.py --platform --delete-data <student_id>    # Delete student data
python main.py --platform --withdraw-consent <consent_id>  # Withdraw consent
```

### Web Server Mode

The application includes an optional web server mode with health check endpoints:

```bash
# Start web server
python main.py --web-server

# Health check endpoints
curl http://localhost:8000/health              # Basic health check
curl http://localhost:8000/health/detailed     # Detailed health + metrics
curl http://localhost:8000/metrics             # Cache and performance metrics
```

**Health Check Features:**
- ✅ Service availability monitoring
- 📊 Cache performance metrics
- 🔍 Dependency status checks
- 📈 System resource monitoring
- 🕒 Uptime and version information

## 📁 Project Structure

```
job-market-analyzer/
├── 📄 main.py                 # Main application entry point
├── 📄 scrapper.py             # Job scraping functionality
├── 📄 requirements.txt        # Python dependencies
├── 📄 Dockerfile             # Docker container configuration
├── 📄 docker-compose.yml     # Docker Compose setup
├── 📄 LICENSE                # MIT license
├── 📄 CV_PLACEHOLDER.txt     # CV file placeholder
├── 📄 env.example           # Environment configuration template
├── 📄 .gitignore            # Git ignore rules
├── 📁 .github/
│   ├── 📁 workflows/        # GitHub Actions CI/CD
│   └── 📄 dependabot.yml    # Dependency updates
├── 📁 agents/               # AI agent implementations
│   ├── 📄 __init__.py
│   ├── 📄 profile_agent.py      # CV analysis agent
│   ├── 📄 job_matcher.py        # Job matching agent
│   ├── 📄 cover_letter_agent.py # Cover letter generation
│   ├── 📄 ats_optimizer_agent.py # ATS optimization
│   ├── 📄 cv_rewriter.py        # CV tailoring
│   ├── 📄 interview_prep_agent.py # Interview preparation
│   └── 📄 interview_copilot_agent.py # Interview assistance
├── 📁 utils/                # Utility modules
│   ├── 📄 __init__.py
│   ├── 📄 scraping.py           # Job scraping utilities
│   ├── 📄 matching.py           # Job matching algorithms
│   ├── 📄 knowledge_base.py     # Knowledge base management
│   ├── 📄 ethical_guidelines.py # Ethical AI guidelines
│   ├── 📄 sa_customizations.py  # South African customizations
│   ├── 📄 cv_tailoring.py       # CV tailoring engine
│   ├── 📄 mock_interview.py     # Interview simulation
│   └── 📄 database.py           # Database utilities
└── 📁 README.md            # This file
```

## ⚙️ Configuration

Copy `env.example` to `.env` and configure:

```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here
CV_FILE_PATH=path/to/your/cv.pdf

# Optional - customize behavior
DEFAULT_LOCATION="San Francisco, CA"
CAREER_GOALS_DEFAULT="I want to become a software engineer"
CACHE_MAX_SIZE_AGENT=500
```

## 🎯 New Advanced Features

### Smart CV Analysis
The system now intelligently analyzes your CV to extract:
- **Career goals** (instead of using defaults)
- **Skill levels** and proficiency ratings
- **Experience assessment** (Entry/Mid/Senior level)
- **Industry preferences**

### Intelligent Job Search
Instead of searching for generic terms, the system now:
- Uses your **extracted career goals** for targeted searches
- Applies **experience-level filtering** (junior/senior roles)
- Includes **skill-based search terms** (Python developer, React engineer)
- Searches **multiple variations** for better results

### Cost Optimization
- **Intelligent caching** reduces API calls by 70-90%
- **Response deduplication** prevents repeated analysis
- **Batch processing** for efficient API usage
- **Cost estimation** displayed before running

### Performance Monitoring
- **Cache hit rates** and performance metrics
- **Progress bars** for long-running operations
- **Real-time statistics** during execution
- **Graceful shutdown** handling (Ctrl+C)

### GDPR/POPIA Compliance
- **Data export functionality** - Complete data portability
- **Right to deletion** - Secure data removal with consent verification
- **Consent management** - Track and withdraw consent
- **Audit trails** - Complete logging of data operations
- **Data retention policies** - 2-year retention with automatic cleanup


## 🚀 Usage

### Command Line Interface

The system provides multiple usage modes through a comprehensive CLI:

```bash
python main.py [OPTIONS]
```

#### Available Commands

**Full Career Analysis Pipeline:**
```bash
python main.py
```
Runs complete workflow: CV analysis → job discovery → AI matching → recommendations

**Quick Job Search:**
```bash
python main.py --search "software engineer" --location "Cape Town"
```

**CV Analysis Only:**
```bash
python main.py --analyze-cv
```

**Interactive Career Platform:**
```bash
python main.py --platform
```
Access the full CareerBoost platform with student onboarding, application tracking, and interview preparation

#### CLI Options

- `--verbose, -v`: Enable verbose output
- `--quiet, -q`: Suppress non-essential output
- `--search QUERY`: Search for specific job roles
- `--location CITY`: Specify location for job search
- `--analyze-cv`: Run CV analysis only
- `--platform`: Launch CareerBoost platform
- `--help`: Show help message

### Python API Usage

#### Job Scraping
```python
from scrapper import scrape_all_advanced, advanced_scraper

# Basic usage with advanced features
jobs = scrape_all_advanced(
    "software engineer",
    "San Francisco, CA",
    site_name=["indeed", "linkedin", "google"],
    results_wanted=50,
    linkedin_fetch_description=True
)

# Advanced filtering and export
premium_jobs = advanced_scraper.filter_jobs(jobs,
    min_relevance=0.7,
    required_skills=['Python', 'JavaScript'],
    min_salary=100000
)

# Export in multiple formats
advanced_scraper.export_jobs(jobs, "my_jobs", "json")
advanced_scraper.export_jobs(premium_jobs, "premium_jobs", "csv")
```

**Advanced Features:**
- **7 Job Sites**: Indeed, LinkedIn, Google, Glassdoor, ZipRecruiter, Naukri, BDJobs
- **Smart Deduplication**: Automatic removal of duplicate jobs
- **Data Enrichment**: Salary parsing, skill extraction, relevance scoring
- **Advanced Filtering**: By skills, salary, location, relevance score
- **Intelligent Caching**: 24-hour cache to avoid redundant scraping
- **Multi-format Export**: JSON, CSV, Excel
- **Comprehensive Logging**: File and console logging

#### CV Tailoring Engine
```python
from utils import CVTailoringEngine

engine = CVTailoringEngine(master_cv="your_cv_content", student_profile=profile)
tailored_cv, ats_score = engine.generate_tailored_cv(job_posting)
cover_letter = engine.generate_cover_letter(job_posting, tailored_cv)
questions = engine.generate_interview_questions(job_posting, tailored_cv)
```

#### Mock Interview Simulator
```python
from utils import MockInterviewSimulator

simulator = MockInterviewSimulator("Software Engineer", "TechCorp", student_profile)
simulator.conduct_interview()
```

#### CareerBoost Platform
```python
from main import CareerBoostPlatform

platform = CareerBoostPlatform()
student_id = platform.onboard_student(cv_content, "Software Engineer", consent_given=True)
jobs = platform.find_matching_jobs(student_id, location="South Africa")
platform.prepare_for_interview(student_id, job_id)
```

## 🏗️ Architecture

### Core Components

#### Main Modules
- **`main.py`**: CLI interface, JobMarketAnalyzer class, and CareerBoostPlatform class
- **`scrapper.py`**: Advanced Playwright-based multi-site job scraping
- **`agents/`**: Specialized AI agents for different career tasks
- **`utils/`**: Utility modules for CV tailoring, interviews, knowledge base, etc.

#### Data Storage
- **`jobs.json`**: Cached scraped job data
- **ChromaDB**: Vector database for semantic search and job storage
- **Knowledge Base**: Structured information repository with embeddings

### AI Agent System

The system uses multiple specialized AI agents, each with specific responsibilities:

#### Career Analysis Agents
1. **Profile Builder** (`agents/profile_agent.py`): Extracts structured profiles from CVs
2. **Job Matcher** (`agents/job_matcher_agent.py`): Multi-dimensional job matching

#### CV & Application Agents
3. **ATS Optimizer** (`agents/ats_optimizer_agent.py`): Analyzes CV ATS compatibility
4. **CV Rewriter** (`agents/cv_rewriter_agent.py`): Tailors CV content for specific jobs
5. **Cover Letter Agent** (`agents/cover_letter_agent.py`): Generates personalized cover letters

#### Interview & Preparation Agents
6. **Interview Prep Agent** (`agents/interview_prep_agent.py`): Predicts interview questions
7. **Interview Copilot** (`agents/interview_copilot_agent.py`): Real-time interview assistance

### Utility Systems

#### CV Tailoring Engine (`utils/cv_tailoring.py`)
- Job-specific CV generation
- ATS optimization
- Cover letter creation
- Interview question prediction
- Version management and export

#### Knowledge Base (`utils/knowledge_base.py`)
- Vector embeddings for semantic search
- SA-specific context and job market intelligence
- Company research and industry insights

#### Mock Interview Simulator (`utils/mock_interview.py`)
- Realistic interview practice
- AI interviewer with behavioral analysis
- Performance feedback and improvement suggestions

#### South African Customizations (`utils/sa_customizations.py`)
- Transport-aware job recommendations
- Cultural and market-specific adjustments
- Location-based salary and commute considerations

#### Ethical Guidelines (`utils/ethical_guidelines.py`)
- Comprehensive AI ethics framework
- Bias mitigation strategies
- Responsible career assistance guidelines

### Scoring Algorithm

Jobs are scored on 4 dimensions with South African context awareness:

- **Aspiration Fit (40%)**: Career goals alignment with cultural considerations
- **Skill Fit (35%)**: Semantic skill matching using embeddings
- **Experience Fit (15%)**: Seniority and background requirements
- **Practical Fit (10%)**: Location, transport, remote work, company culture

**Additional SA Factors:**
- Transport accessibility and cost
- Work permit requirements
- Salary expectations in local context
- Company reputation and work culture

### Data Flow Architecture

```
CV Upload → Profile Analysis → Job Discovery → AI Matching → Recommendations
    ↓            ↓              ↓            ↓              ↓
PDF/Text   → Structured Data → Vector DB   → Scoring     → Ranked Jobs
    ↓            ↓              ↓            ↓              ↓
Tailoring   → CV Versions    → Applications → Interviews  → Offers
```

#### Detailed Flow:
1. **CV Processing**: PDF → Text → AI Analysis → Structured Profile → Skill Gap Analysis
2. **Job Discovery**: Multi-site scraping → Deduplication → ChromaDB storage → Semantic indexing
3. **Intelligent Matching**: Profile comparison → Multi-dimensional scoring → SA customization → Rankings
4. **Application Support**: CV tailoring → Cover letter generation → ATS optimization → Application tracking
5. **Interview Preparation**: Question prediction → Mock interviews → Performance analysis → Skill development

## 🔧 Troubleshooting

### Common Issues

1. **Missing API Key**: Ensure `GOOGLE_API_KEY` is set in `.env` or environment variables
2. **CV Path Error**: `CV_FILE_PATH` will default to `CV.pdf` if the file exists in the current directory
3. **Import Errors**: Run `pip install -r requirements.txt` and `python -m playwright install`
4. **Scraping Failures**: Websites may have changed; check debug PNG/HTML files in the directory
5. **Browser Issues**: Run `python -m playwright install` to install browser binaries
6. **API Rate Limiting**: Gemini API has usage limits; the system includes fallback modes
7. **Knowledge Base Issues**: Run the system once to initialize the vector database collections
8. **Memory Issues**: Large CVs or many job results may require more RAM

### Debug Features

#### Scraping Debug Files
- `*_debug.png`: Screenshots of scraping state
- `*_debug.html`: Page HTML for selector inspection
- `pnet_debug.*`, `indeed_debug.*`, `careerjunction_debug.*`: Site-specific debug files

#### Verbose Logging
```bash
python main.py --verbose  # Enable detailed logging
```

#### Platform Testing
```python
python test_complete.py  # Test the complete job matching pipeline
```

## 🤝 Contributing

We welcome contributions to the Job Market AI Analyzer! Here's how you can help:

### Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch**: `git checkout -b feature/your-feature-name`
4. **Set up development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development dependencies
   ```

### Development Workflow

1. **Make your changes** following our coding standards
2. **Run tests**: `pytest`
3. **Check code quality**: `flake8` and `black`
4. **Test your changes** thoroughly
5. **Commit with clear messages**: `git commit -m "feat: add new feature"`
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Create a Pull Request** on GitHub

### Coding Standards

- **Python**: Follow PEP 8 style guidelines
- **Type Hints**: Add type annotations to all functions
- **Documentation**: Document all public functions and classes
- **Testing**: Write tests for new features
- **Commits**: Use conventional commit format

### Areas for Contribution

- 🐛 **Bug Fixes**: Help us squash bugs and improve stability
- ✨ **New Features**: Add new AI agents or functionality
- 📚 **Documentation**: Improve docs, tutorials, or examples
- 🧪 **Testing**: Write more comprehensive tests
- 🎨 **UI/UX**: Improve the command-line interface
- 🌐 **Internationalization**: Add support for more languages
- 📊 **Analytics**: Add better metrics and reporting

### Reporting Issues

When reporting bugs or requesting features:
- Use the issue templates provided
- Include detailed steps to reproduce
- Provide system information (OS, Python version, etc.)
- Attach relevant log files or screenshots

Thank you for contributing to making job searching smarter! 🚀

## 📦 Dependencies

### Core Dependencies
- `agno`: AI agent framework for specialized career assistance
- `google-genai`: Google Gemini AI models for analysis and generation
- `chromadb`: Vector database for semantic search and job storage
- `playwright`: Browser automation for reliable web scraping
- `PyMuPDF`: PDF processing for CV analysis

### Additional Libraries
- `python-dotenv`: Environment variable management
- `typing`: Type hints for better code documentation
- `datetime`: Date and time handling for application tracking
- `uuid`: Unique identifier generation for students and applications
- `os`, `sys`, `argparse`: Standard library utilities

### Development Dependencies
- Testing frameworks and linting tools as needed

## 🤝 Contributing

This project welcomes contributions! Areas for improvement:

- Additional South African job sites integration
- Enhanced CV parsing for different formats
- More sophisticated interview scenarios
- Expanded knowledge base with industry insights
- Performance optimizations for large-scale usage

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper testing
4. Ensure all linting passes
5. Submit a pull request

## 🙏 Acknowledgments

- Google Gemini for AI capabilities
- South African job platforms for career opportunities
- Open source community for the amazing tools and libraries

## 📄 License

This project is for educational purposes. Respect website terms of service when scraping and API usage limits when using AI services. The system includes comprehensive ethical guidelines to ensure responsible AI assistance.
