# Job Market Agent - Automated Application Pipeline

An intelligent, automated job application system that finds jobs, generates optimized CVs and cover letters, and prepares interview materials.

## 🚀 Quick Start

### Prerequisites
1. Python 3.8+
2. Google API Key (for Gemini AI)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up your API key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Basic Usage

Run the automated pipeline:

```bash
python main.py
```

This will:
1. Load your CV from `cvs/CV.pdf`
2. Search for "Python Developer" jobs in "South Africa"
3. Generate 3 optimized applications (CV + cover letter)
4. Create interview preparation materials
5. Save everything to the `applications/` folder

## 📋 Command Line Options

```bash
# Custom job search
python main.py --query "Data Scientist" --location "Cape Town"

# Generate more applications
python main.py --max 5

# Use a different CV
python main.py --cv path/to/your/cv.pdf

# Combine options
python main.py --query "Software Engineer" --location "Johannesburg" --max 10
```

## 🎯 Features

### 1. **Intelligent Job Search**
- Scrapes jobs from LinkedIn and Indeed
- Stores job history in ChromaDB
- Avoids duplicate applications

### 2. **AI-Powered Profile Building**
- Analyzes your CV
- Extracts skills, experience, and career goals
- Creates a comprehensive candidate profile

### 3. **Smart Job Ranking**
- Ranks jobs based on your profile
- Provides match scores (0-100)
- Explains why each job is a good fit

### 4. **Automated Application Generation**
- Creates job-specific optimized CVs
- Generates personalized cover letters
- Ensures ATS compatibility
- Saves applications to `applications/` folder

### 5. **Interview Preparation**
- Generates likely interview questions
- Provides suggested answers
- Lists questions to ask the interviewer

## 📁 Project Structure

```
Job-Market-Agent/
├── main.py                 # Automated pipeline (NEW!)
├── main_swarm.py          # Interactive chat interface
├── agents/                # AI agents
│   ├── profile_agent.py
│   ├── job_intelligence_agent.py
│   ├── application_writer_agent.py
│   ├── interview_prep_agent.py
│   └── orchestrator_agent.py
├── utils/                 # Utilities
│   ├── memory_store.py    # ChromaDB integration
│   ├── scraping.py        # Job scraping
│   └── cv_tailoring.py    # CV generation
├── services/
│   └── watcher.py         # Background job monitoring
├── applications/          # Generated applications (auto-created)
├── cvs/                   # Your CV files
└── requirements.txt
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional
CV_FILE_PATH=cvs/CV.pdf
SEARCH_QUERY=Python Developer
LOCATION=South Africa
MAX_JOBS=10
```

## 💡 Usage Examples

### Example 1: Entry-Level Developer
```bash
python main.py \
  --query "Junior Python Developer" \
  --location "Cape Town" \
  --max 5
```

### Example 2: Data Science Role
```bash
python main.py \
  --query "Data Scientist" \
  --location "Johannesburg" \
  --max 3
```

### Example 3: Remote Jobs
```bash
python main.py \
  --query "Remote Software Engineer" \
  --location "South Africa" \
  --max 10
```

## 📊 Output

The pipeline creates files in the `applications/` folder:

```
applications/
├── Google_Software_Engineer_20250119_153045.txt
├── Interview_Prep_Google_20250119.txt
├── Microsoft_Data_Scientist_20250119_153120.txt
├── Interview_Prep_Microsoft_20250119.txt
└── ...
```

Each application file contains:
- Optimized CV tailored to the job
- Personalized cover letter
- ATS compatibility score
- Job details and URL

## 🤖 Interactive Mode

For a conversational experience, use the Swarm interface:

```bash
python main_swarm.py
```

Then chat with the Career Concierge:
- "Find me a Python job in Cape Town"
- "Rewrite my CV for this job description: ..."
- "Prepare me for an interview at Google"

## 🔄 Background Monitoring

Run the watcher service for 24/7 job monitoring:

```bash
python services/watcher.py
```

This will check for new jobs every 6 hours and log alerts.

## 🏗️ Architecture

The system uses a **consolidated agent architecture**:

1. **Profile Builder** - Analyzes your background
2. **Job Intelligence** - Finds and ranks jobs
3. **Application Writer** - Creates CVs and cover letters
4. **Interview Coach** - Prepares interview materials
5. **Orchestrator** - Coordinates all agents

## 📝 Notes

- **Rate Limiting**: The system includes built-in delays to respect API limits
- **Memory**: Jobs are stored in ChromaDB to avoid duplicates
- **Privacy**: All data is stored locally
- **Customization**: Edit agent instructions in `agents/` to customize behavior

## 🐛 Troubleshooting

### "CV not found"
Make sure your CV is at `cvs/CV.pdf` or specify the path with `--cv`

### "GOOGLE_API_KEY not found"
Create a `.env` file and add your API key:
```bash
GOOGLE_API_KEY=your_key_here
```

### "No jobs found"
Try a different search query or location:
```bash
python main.py --query "Developer" --location "Remote"
```

## 📚 Documentation

- [API Setup Guide](API_SETUP.md)
- [Docker Build Guide](DOCKER_BUILD_GUIDE.md)
- [Rate Limiting Guide](RATE_LIMITING_GUIDE.md)

## 📄 License

See [LICENSE](LICENSE) file for details.

---

**Made with ❤️ for job seekers in South Africa**