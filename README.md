---
title: FastAPI
description: A FastAPI server
tags:
  - fastapi
  - hypercorn
  - python
---

# FastAPI Application

A production-ready FastAPI server with automated deployment to Synology NAS.

## Features

- FastAPI with [Hypercorn](https://hypercorn.readthedocs.io/) ASGI server
- Python 3.12+
- Docker containerization
- Automated CI/CD with GitHub Actions
- Production-level environment variable management
- Synology NAS deployment

## Quick Start

### Local Development

1. **Clone and install dependencies**:
   ```bash
   git clone <repository-url>
   cd demo-fastapi
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp env.example .env.local
   # Edit .env.local with your development values
   ```

3. **Run locally**:
   ```bash
   python main.py
   # or
   ./build.sh
   ```

### Production Deployment

Deploy to production with a single command:

```bash
# Set up your production environment
cp env.example .env.production
# Edit .env.production with your actual production values

# Deploy everything automatically
./scripts/deploy.sh .env.production
```

This will:
- ✅ Validate your environment setup
- ✅ Handle git operations (add, commit, push)
- ✅ Upload secrets to GitHub
- ✅ Trigger automated deployment
- ✅ Monitor deployment progress

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete production deployment guide
- **[FastAPI Documentation](https://fastapi.tiangolo.com/tutorial/)** - Learn FastAPI features
- **[Hypercorn Documentation](https://hypercorn.readthedocs.io/)** - ASGI server configuration

## Architecture

- **Application**: FastAPI with async support
- **Server**: Hypercorn ASGI server
- **Containerization**: Docker with multi-stage builds
- **Deployment**: GitHub Actions → Docker Hub → Synology NAS
- **Secrets**: GitHub Secrets with automated upload
- **Monitoring**: Health checks and logging