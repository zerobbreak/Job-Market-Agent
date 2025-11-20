# 🚀 Docker Build Optimization Guide

## Overview

This guide provides multiple Docker build configurations optimized for different use cases - from fast development builds to optimized production deployments.

## 📊 Build Performance Comparison

| Build Type | Build Time | Image Size | Use Case |
|------------|------------|------------|----------|
| **Development** | 3-5 minutes | ~2GB | Fast iteration, testing |
| **Production (Optimized)** | 12-18 minutes | ~8GB | Full features, caching |
| **Multi-Stage** | 15-20 minutes | ~4GB | Production, smaller image |
| **Legacy** | 20-30 minutes | ~10GB | Original Dockerfile |

## 🛠️ Build Configurations

### 1. 🚀 Development Build (Fastest)

**Perfect for development and testing**

```bash
# Build development image
docker-compose --profile development build

# Run development container
docker-compose --profile development up

# Or use directly
docker build -f Dockerfile.dev -t job-market-dev .
docker run -it --rm --env-file .env -v $(pwd)/CV.pdf:/app/CV.pdf:ro job-market-dev
```

**What's included:**
- ✅ Core AI functionality (Agno, Google AI)
- ✅ Basic ML libraries (scikit-learn, XGBoost)
- ✅ Job scraping (without Playwright browsers)
- ✅ PDF processing, data handling
- ❌ Heavy ML (PyTorch, Transformers, SpaCy)
- ❌ Playwright browser automation

### 2. 🏭 Production Build (Optimized)

**Best for production with full features**

```bash
# Build optimized production image
docker-compose build

# Or use BuildKit for faster builds
DOCKER_BUILDKIT=1 docker-compose build

# Run production container
docker-compose up
```

**Optimizations:**
- ✅ Layered dependency installation (lightweight → heavy)
- ✅ Better Docker layer caching
- ✅ All features included
- ✅ Optimized build order

### 3. 📦 Multi-Stage Build (Smallest)

**Production build with minimal image size**

```bash
# Build multi-stage image
docker-compose --profile multi-stage build

# Run multi-stage container
docker-compose --profile multi-stage up
```

**Benefits:**
- ✅ Smaller final image (~4GB vs ~8GB)
- ✅ Isolated build environment
- ✅ Virtual environment isolation
- ✅ All features included

### 4. 🐌 Legacy Build (Original)

**Original Dockerfile for compatibility**

```bash
# Use original Dockerfile (slower)
docker build -f Dockerfile.original -t job-market-legacy .
```

## ⚡ Quick Start Commands

### Development (Fast)
```bash
# 3-5 minute build
docker-compose --profile development build
docker-compose --profile development run --rm job-market-analyzer python main.py --help
```

### Production (Full Features)
```bash
# 12-18 minute build (with caching)
DOCKER_BUILDKIT=1 docker-compose build
docker-compose up
```

### Multi-Stage (Small Image)
```bash
# 15-20 minute build
docker-compose --profile multi-stage build
docker-compose --profile multi-stage up
```

## 🔧 Advanced Configuration

### Environment Variables

```bash
# Development mode
export DEV_MODE=true

# Production mode
export PRODUCTION=true

# Multi-stage mode
export MULTI_STAGE=true
```

### Custom Builds

```bash
# Build with specific target
docker build --target runtime -f Dockerfile.multi -t custom-build .

# Build with build args
docker build --build-arg BUILDKIT_INLINE_CACHE=1 -t cached-build .
```

### Build Caching

```bash
# Use build cache from previous builds
docker build --cache-from job-market-analyzer:latest -t job-market-analyzer .

# Export/import cache
docker buildx build --cache-to type=local,dest=/tmp/cache --cache-from type=local,src=/tmp/cache .
```

## 🐛 Troubleshooting

### Build Failures

**Issue: Heavy ML libraries timeout**
```bash
# Solution: Use development build first
docker-compose --profile development build
```

**Issue: Playwright browser installation fails**
```bash
# Solution: Skip Playwright in dev builds
# Use development profile
```

### Performance Issues

**Slow builds on Windows:**
```powershell
# Enable BuildKit
$env:DOCKER_BUILDKIT=1
docker-compose build
```

**Out of disk space:**
```bash
# Clean up old images
docker system prune -a

# Remove build cache
docker builder prune -a
```

## 📋 Feature Matrix

| Feature | Development | Production | Multi-Stage |
|---------|-------------|------------|-------------|
| Core AI (Agno) | ✅ | ✅ | ✅ |
| Google AI | ✅ | ✅ | ✅ |
| Basic ML | ✅ | ✅ | ✅ |
| Heavy ML (PyTorch) | ❌ | ✅ | ✅ |
| NLP (SpaCy) | ❌ | ✅ | ✅ |
| Job Scraping | ✅ | ✅ | ✅ |
| Playwright | ❌ | ✅ | ✅ |
| PDF Processing | ✅ | ✅ | ✅ |
| Caching | Basic | Optimized | Advanced |
| Image Size | ~2GB | ~8GB | ~4GB |
| Build Time | 3-5min | 12-18min | 15-20min |

## 🎯 Recommendations

### For Development
- Use **Development Build** for fast iteration
- Add features incrementally
- Test with slim dependencies first

### For Production
- Use **Production Build** for full functionality
- Enable BuildKit for faster builds
- Use multi-stage for smaller deployments

### For CI/CD
- Use **Multi-Stage Build** for smaller images
- Cache layers between builds
- Use development build for testing

## 🚀 Getting Started

1. **Clone repository**
2. **Set up environment**: `cp .env.example .env`
3. **Choose build type** based on your needs
4. **Build and run**:
   ```bash
   # Development (fast)
   docker-compose --profile development up --build

   # Production (full features)
   docker-compose up --build

   # Multi-stage (small image)
   docker-compose --profile multi-stage up --build
   ```

Choose the build configuration that best fits your workflow! 🎉
