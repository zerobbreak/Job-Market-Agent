# =============================================================================
# Job Market AI Analyzer - Optimized Production Dockerfile
# =============================================================================
# Optimized for better caching and faster rebuilds while maintaining full functionality

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PRODUCTION=true

# Install system dependencies with better caching
RUN apt-get update && apt-get install -y \
    # Required for PyMuPDF (fitz)
    build-essential \
    libpoppler-cpp-dev \
    pkg-config \
    python3-dev \
    # Required for Playwright
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy and install dependencies in layers for better caching
COPY requirements.txt .

# Install dependencies in optimized order (lightweight first)
RUN pip install --no-cache-dir \
    # Install lightweight packages first (for better caching)
    requests==2.32.5 \
    httpx==0.28.1 \
    tenacity==9.1.2 \
    tqdm==4.67.1 \
    rich==14.2.0 \
    click==8.3.0 \
    colorama==0.4.6 \
    python-dotenv==1.1.1 \
    fastapi==0.115.0 \
    uvicorn==0.24.0 \
    numpy==1.26.3 \
    pandas==2.3.3 \
    beautifulsoup4==4.14.2 \
    cachetools==6.2.1 \
    PyMuPDF==1.26.5 \
    reportlab==4.2.5 \
    pytest==7.4.0 \
    && pip install --no-cache-dir \
    # Core AI/ML (medium weight)
    agno==2.2.1 \
    google-genai==1.46.0 \
    google-generativeai==0.8.3 \
    scikit-learn==1.5.2 \
    xgboost==2.1.3 \
    nltk==3.9.1 \
    joblib==1.4.2 \
    pydantic==2.12.3 \
    pydantic-settings==2.11.0 \
    && pip install --no-cache-dir \
    # Heavy ML libraries (install last to maximize cache reuse)
    torch==2.5.1 \
    transformers==4.46.3 \
    sentence-transformers==3.3.1 \
    spacy==3.8.2 \
    chromadb==1.2.1 \
    python-jobspy==1.1.82 \
    && pip install --no-cache-dir \
    # Additional ML utils (if available)
    scipy==1.13.0 \
    matplotlib==3.8.4 \
    seaborn==0.13.2 \
    psutil==5.9.8 \
    gputil==1.4.0 \
    shap==0.45.0 \
    lime==0.2.0.1 \
    aif360==0.6.1 \
    imbalanced-learn==0.12.4

# Install Playwright browsers (after dependencies to avoid conflicts)
RUN python -m playwright install --with-deps chromium

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port for web server mode
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import main; print('Health check passed')" || exit 1

# Default command
CMD ["python", "main.py", "--help"]
