# CareerBoost AI - Complete Job Market Analysis System

🎯 **Advanced AI-powered career acceleration platform for South African students and professionals**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-red.svg)](LICENSE)

## 🌟 Overview

CareerBoost AI is a comprehensive career acceleration system that integrates multiple specialized AI agents and utilities to provide end-to-end career support. From CV analysis to interview preparation, this system helps South African students and professionals navigate the job market with AI-powered insights and personalized recommendations.

## 🤖 AI Agents

The system features **6 specialized AI agents** working in coordination:

### 1. **Career Intelligence Analyst** (`profile_agent.py`)
- **Purpose**: Comprehensive 360° student profile mapping
- **Capabilities**:
  - Academic background analysis
  - Work experience evaluation
  - Technical skills assessment
  - Career aspiration mapping
  - South African context considerations
  - Growth trajectory prediction

### 2. **Opportunity Discovery Engine** (`job_matcher_agent.py`)
- **Purpose**: Intelligent job matching with sophisticated scoring
- **Capabilities**:
  - Multi-dimensional job scoring (100-point system)
  - Aspiration alignment analysis
  - Qualification fit assessment
  - Practical viability evaluation
  - SA-specific transport and economic considerations

### 3. **ATS Optimization Specialist** (`ats_optimizer_agent.py`)
- **Purpose**: ATS compatibility analysis and optimization
- **Capabilities**:
  - Format compliance checking
  - Keyword density analysis
  - Action verb optimization
  - Achievement quantification
  - SA-specific formatting guidelines

### 4. **CV Content Strategist** (`cv_rewriter_agent.py`)
- **Purpose**: Content optimization while maintaining authenticity
- **Capabilities**:
  - Experience elevation and reframing
  - Achievement quantification
  - Skills section optimization
  - Professional summary tailoring
  - Ethical content validation

### 5. **Cover Letter Storyteller** (`cover_letter_agent.py`)
- **Purpose**: Compelling narrative-driven cover letters
- **Capabilities**:
  - Hook-based opening paragraphs
  - STAR method integration
  - Company research incorporation
  - SA-specific cultural references
  - Conversion-optimized language

### **Removed: Interview Intelligence Coach**
The interview preparation agent has been removed due to functionality issues. Interview preparation features are now handled through the Mock Interview Simulator utility.

## 🛠️ Utility Modules

### Core Utilities (`utils/`)

#### **CV Tailoring Engine** (`cv_tailoring.py`)
- Job-specific CV customization
- ATS optimization
- Ethical validation
- Multi-format support

#### **Mock Interview Simulator** (`mock_interview.py`)
- Realistic interview scenarios
- Interview Copilot hints
- Performance analytics
- Confidence building

#### **Knowledge Base** (`knowledge_base.py`)
- Semantic search capabilities
- Multi-source information integration
- Context-aware responses
- Continuous learning

#### **South African Customizations** (`sa_customizations.py`)
- Transport cost calculations
- BEE/EE compliance insights
- Local market intelligence
- Cultural context adaptation

#### **Ethical Guidelines** (`ethical_guidelines.py`)
- POPIA/GDPR compliance
- Data consent management
- Application ethics validation
- Transparency reporting

#### **Job Database & Matching** (`database.py`, `matching.py`)
- Efficient job storage and retrieval
- Advanced matching algorithms
- Performance optimization
- Real-time updates

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.8+
python --version

# Required packages
pip install -r requirements.txt
```

### Environment Setup

1. **Create environment file**:
```bash
cp env.example .env
```

2. **Configure API keys**:
```bash
# Edit .env file
GOOGLE_API_KEY=your_google_api_key_here
CV_FILE_PATH=CV.pdf  # Optional: path to your CV
```

### Running the Application

#### Interactive Mode (Recommended)
```bash
python main.py --interactive
```

#### Automated Demonstration
```bash
python main.py --demo
```

#### Platform Mode
```bash
# Onboard a student
python main.py --platform --onboard CV.pdf --goals "Become a software engineer"

# Find matching jobs
python main.py --platform --student-id ABC123 --find-jobs

# Prepare application
python main.py --platform --student-id ABC123 --apply JOB_ID

# Interview preparation
python main.py --platform --student-id ABC123 --interview-prep JOB_ID
```

## 📋 Usage Guide

### 1. Student Onboarding
```bash
python main.py --interactive
# Select option 1: Student Onboarding
# Enter CV path: CV.pdf
# Enter career goals: Become a data scientist
```

### 2. Job Discovery & Matching
```bash
python main.py --interactive
# Select option 2: Job Discovery & Matching
# Enter Student ID: (from onboarding)
```

### 3. Application Preparation
```bash
python main.py --interactive
# Select option 3: Application Preparation
# Enter Student ID and Job ID
```

### 4. Interview Preparation
```bash
python main.py --interactive
# Select option 4: Interview Preparation
# Enter Student ID and Job ID
```

## 🎯 Key Features

### 🤖 **Intelligent AI Coordination**
- Agents work together seamlessly
- Context sharing between operations
- Ethical decision-making throughout

### 🇿🇦 **South African Focus**
- Transport cost considerations
- BEE/EE transformation insights
- Local market intelligence
- Cultural context awareness

### 🛡️ **Ethical & Compliant**
- POPIA/GDPR compliance
- Transparent AI usage
- Data consent management
- Ethical application practices

### 📊 **Performance Optimized**
- Advanced caching system
- Intelligent API management
- Real-time performance monitoring
- Cost optimization

### 🎓 **Education-First Approach**
- Skills gap analysis
- Learning pathway recommendations
- Realistic career expectations
- Continuous development focus

## 🏗️ System Architecture

```
CareerBoost AI Platform
├── 🤖 AI Agents (5 specialized agents)
├── 🛠️ Utility Modules (8 core utilities)
├── 💾 Data Layer (Job database, Knowledge base)
├── 🔒 Security Layer (Ethical guidelines, POPIA compliance)
└── 🎯 User Interface (CLI, Interactive, API)
```

## 📈 Performance & Cost

### Estimated Costs (Gemini 2.0 Flash)
- **CV Analysis**: $0.001-0.003 per run
- **Job Matching**: $0.002-0.005 per run
- **Cover Letter**: $0.003-0.007 per run
- **Total per complete analysis**: $0.006-0.015

### Performance Features
- **Intelligent Caching**: 30-50% cost reduction
- **Response Deduplication**: Eliminates redundant API calls
- **Batch Processing**: Optimized for multiple operations
- **Real-time Monitoring**: Performance tracking and optimization

## 🔧 Configuration

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional
CV_FILE_PATH=CV.pdf
CAREER_GOALS_DEFAULT=Become a software engineer
DEFAULT_LOCATION=South Africa
DEFAULT_INDUSTRY=Technology

# Caching
CACHE_AGENT_TTL=1800
CACHE_JOB_TTL=86400
CACHE_PROFILE_TTL=3600

# API Settings
API_MAX_RETRIES=3
API_RETRY_DELAY=2.0
API_TIMEOUT=30

# Scraping
MAX_JOBS_PER_SITE=50
MAX_SEARCH_TERMS=5
SCRAPING_TIMEOUT=60
```

### Advanced Configuration

```bash
# Web server mode
python main.py --web-server --port 8080

# Health monitoring
curl http://localhost:8080/health
curl http://localhost:8080/health/detailed
curl http://localhost:8080/metrics
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-repo/careerboost-ai.git
cd careerboost-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Run tests
pytest

# Run linting
flake8
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Agno Framework](https://github.com/agno-ai/agno)
- Powered by [Google Gemini](https://ai.google.dev/)
- South African market insights and ethical guidelines
- Community contributions and feedback

## 📞 Support

- **Documentation**: [Full Documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email**: support@careerboost.ai

---

**CareerBoost AI** - Accelerating careers through intelligent automation 🇿🇦</content>
</xai:function_call">