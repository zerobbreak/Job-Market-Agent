# Job Market AI Analysis System

A comprehensive AI-powered career platform designed for South African students, featuring advanced job matching, CV optimization, interview preparation, and ethical AI assistance. The system integrates multiple specialized AI agents to provide end-to-end career support.

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

## Setup

### Prerequisites

- Python 3.11+
- Google Gemini API key

### Installation

1. **Clone and install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers**:
   ```bash
   python -m playwright install
   ```

3. **Set up environment variables**:
   ```bash
   cp env.example .env
   ```

   Edit `.env` with your actual values:
   ```
   GOOGLE_API_KEY=your_actual_google_api_key
   CV_FILE_PATH=path/to/your/cv.pdf
   CAREER_GOALS=your career aspirations
   ```

   Or set environment variables directly:
   ```bash
   export GOOGLE_API_KEY=your_key_here
   export CV_FILE_PATH=CV.pdf
   ```

### Google Gemini API Setup

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

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
from scrapper import scrape_all
jobs = scrape_all("software engineer", "Johannesburg")
```

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
