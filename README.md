# Job Market AI Analysis System

An AI-powered job matching system that scrapes South African job sites and matches student profiles with relevant opportunities using advanced semantic analysis.

## Features

- **AI-Powered CV Analysis**: Uses Google Gemini to extract structured profiles from PDF CVs
- **Multi-Site Job Scraping**: Scrapes jobs from PNet, CareerJunction, and Indeed South Africa
- **Semantic Skill Matching**: Uses embeddings to match skills beyond exact keyword matching
- **Vector Database**: Stores jobs in ChromaDB for efficient similarity search
- **Multi-Dimensional Scoring**: 4-factor matching algorithm (Aspiration, Skills, Experience, Practical)

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

## Usage

### Basic Job Matching

```python
python main.py
```

This will:
1. Analyze your CV using AI
2. Scrape current jobs from major South African sites
3. Match jobs to your profile with detailed scoring
4. Display ranked recommendations

### Job Scraping Only

```python
from scrapper import scrape_all
jobs = scrape_all("software engineer", "Johannesburg")
```

### Integrated Usage

The `main.py` now integrates the advanced scraping from `scrapper.py`:

```python
python main.py  # Runs full pipeline: CV analysis → job scraping → AI matching
```

The system automatically:
1. Analyzes your CV using AI
2. Scrapes jobs from multiple sites using Playwright
3. Matches jobs to your profile with detailed scoring
4. Stores results in the vector database

## Architecture

### Components

- **`main.py`**: Core AI matching logic, job analysis, and integrated scraping
- **`scrapper.py`**: Advanced Playwright-based web scraping module
- **`jobs.json`**: Cached scraped job data

### AI Agents

1. **Profile Builder**: Extracts education, experience, skills, and aspirations from CVs
2. **Job Matcher**: Performs detailed multi-dimensional job matching

### Scoring Algorithm

Jobs are scored on 4 dimensions (weighted):
- **Aspiration Fit (40%)**: Career goals alignment
- **Skill Fit (35%)**: Semantic skill matching using embeddings
- **Experience Fit (15%)**: Seniority and background requirements
- **Practical Fit (10%)**: Location, remote work, company culture

## Data Flow

1. **CV Processing**: PDF → Text → AI Analysis → Structured Profile
2. **Job Discovery**: Multi-site scraping → ChromaDB vector storage
3. **Matching**: Semantic search → AI scoring → Ranked recommendations

## Troubleshooting

### Common Issues

1. **Missing API Key**: Ensure `GOOGLE_API_KEY` is set in `.env` or environment variables
2. **CV Path Error**: `CV_FILE_PATH` will default to `CV.pdf` if the file exists in the current directory
3. **Import Errors**: Run `pip install -r requirements.txt` and `python -m playwright install`
4. **Scraping Failures**: Websites may have changed; check debug PNG/HTML files in the directory
5. **Browser Issues**: Run `python -m playwright install` to install browser binaries

### Debug Mode

Scraping creates debug files:
- `*_debug.png`: Screenshots of scraping state
- `*_debug.html`: Page HTML for selector inspection

## Dependencies

Key packages:
- `agno`: AI agent framework
- `google-genai`: Gemini AI models
- `chromadb`: Vector database
- `playwright`: Browser automation
- `PyMuPDF`: PDF processing

## License

This project is for educational purposes. Respect website terms of service when scraping.
