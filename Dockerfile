FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Install build dependencies for pycairo and git for GitHub packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libcairo2-dev \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Remove build-only dependencies, keep runtime libraries and git (needed for jobspy updates)
RUN apt-get update && apt-get purge -y gcc python3-dev libcairo2-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . .
CMD ["sh", "-c", "gunicorn api_server:app --bind 0.0.0.0:${PORT:-8000} --timeout 120"]
