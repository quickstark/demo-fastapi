---
title: FastAPI
description: A FastAPI server
tags:
  - fastapi
  - hypercorn
  - python
---

# FastAPI Multi-Service Application

A production-ready FastAPI server with integrated services for file storage, databases, AI processing, and monitoring.

## 🚀 Features

### **Core Application**
- **FastAPI** with Hypercorn ASGI server
- **Docker** containerization with multi-stage builds  
- **Automated CI/CD** with GitHub Actions
- **Environment-based configuration** for dev/staging/production

### **Integrated Services**
- **Amazon S3** - File storage & management
- **MongoDB** - Document database with graceful degradation
- **PostgreSQL** - Primary database
- **OpenAI API** - AI text processing and chat completions
- **YouTube Integration** - Video transcript processing and Notion saving
- **Amazon SES** - Email notifications
- **Notion API** - Content management integration

### **Monitoring & Observability**
- **Datadog** tracing and monitoring
- **LLM Observability** for AI model tracking
- **Runtime metrics** and performance monitoring
- **Custom error tracking** with structured logging

### **Testing Infrastructure**
- **Pytest** with async support
- **Test markers** for different test types (unit, integration, api, etc.)
- **Graceful degradation testing** for external services
- **Datadog Test Optimization** integration

## 📋 API Endpoints

### **Image Management**
- `GET /images` - Retrieve all images (MongoDB or PostgreSQL)
- `POST /add_image` - Upload image to S3 with metadata storage
- `DELETE /delete_image/{id}` - Remove image and metadata

### **AI & Content Processing**  
- `POST /api/v1/chat` - OpenAI chat completions
- `POST /api/v1/save-youtube-to-notion` - Process YouTube videos to Notion

### **Database Operations**
- `GET /api/v1/mongo/test` - MongoDB connection test
- `GET /api/v1/postgres/test` - PostgreSQL connection test

### **System**
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /timeout-test` - Testing endpoint with configurable timeout

## 🛠️ Quick Start

### **Local Development**

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

3. **Run the application**:
   ```bash
   python main.py
   # or using the build script
   ./scripts/build.sh
   ```

### **Production Deployment**

Deploy to production with a single command:

```bash
# Set up your production environment
cp env.example .env.production
# Edit .env.production with your actual production values

# Deploy automatically
./scripts/deploy.sh .env.production
```

**The deployment script handles:**
- ✅ Environment validation and prerequisite checks
- ✅ Git operations (add, commit, push)
- ✅ GitHub Secrets upload
- ✅ Deployment monitoring and verification

## 🧪 Testing

### **Run Tests**

```bash
# Run all tests
pytest

# Run specific test types
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests
pytest -m "not slow"     # Exclude slow tests

# Run with Datadog integration (requires DD_API_KEY)
./scripts/test.sh
```

### **Test Organization**

Tests are organized with pytest markers:
- `@pytest.mark.unit` - Fast unit tests, no external dependencies
- `@pytest.mark.integration` - Tests requiring external services
- `@pytest.mark.slow` - Tests taking >1 second to run
- `@pytest.mark.mongo` - MongoDB-specific tests
- `@pytest.mark.postgres` - PostgreSQL-specific tests
- `@pytest.mark.api` - API endpoint tests

## ⚙️ Configuration

### **Required Environment Variables**

```bash
# Database Configuration
MONGO_CONN=your-mongodb-connection-string
MONGO_USER=your-mongodb-username  
MONGO_PW=your-mongodb-password
PGHOST=your-postgres-host
PGDATABASE=your-database-name
PGUSER=your-postgres-username
PGPASSWORD=your-postgres-password

# API Keys
OPENAI_API_KEY=sk-your-openai-api-key
DATADOG_API_KEY=your-datadog-api-key
DATADOG_APP_KEY=your-datadog-app-key

# Email notifications (Amazon SES)
SES_REGION=us-east-1
SES_FROM_EMAIL=your-verified-email@domain.com
# Note: Uses existing AWS credentials (AMAZON_KEY_ID/AMAZON_KEY_SECRET)

# Notion integration
NOTION_API_KEY=secret_your-notion-key

# AWS Configuration
AMAZON_KEY_ID=your-aws-access-key
AMAZON_KEY_SECRET=your-aws-secret-key
AMAZON_S3_BUCKET=your-s3-bucket-name

# Application Settings
DD_SERVICE=fastapi-app
DD_ENV=production
DD_VERSION=1.0
BUG_REPORT_EMAIL=your-bug-report-email
```

### **GitHub Secrets Management**

For automated deployment, upload your environment variables as GitHub Secrets:

```bash
# Using the setup script
./scripts/setup-secrets.sh .env.production
```

This script automatically uploads all environment variables from your `.env.production` file to GitHub Secrets.

## 🐳 Docker

### **Local Docker Development**

```bash
# Build and run locally
docker build -t fastapi-app .
docker run -p 8000:8000 --env-file .env.local fastapi-app
```

### **Docker Compose**

```bash
# For local development with services
docker-compose up
```

## 📁 Project Structure

```
demo-fastapi/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── pytest.ini            # Test configuration
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Local development services
├── scripts/               # Deployment and utility scripts
│   ├── deploy.sh         # Production deployment automation
│   ├── setup-secrets.sh  # GitHub Secrets management
│   ├── test.sh           # Test runner with Datadog integration
│   └── build.sh          # Local development script
├── src/                   # Application modules
│   ├── amazon.py         # S3 integration
│   ├── mongo.py          # MongoDB operations
│   ├── postgres.py       # PostgreSQL operations
│   ├── openai_service.py # OpenAI API integration
│   ├── datadog.py        # Monitoring and observability
│   └── services/         # Additional service integrations
└── tests/                # Test suite
    ├── conftest.py       # Test configuration and fixtures
    ├── test_basic.py     # API endpoint tests
    ├── test_simple.py    # Unit tests
    └── mongo_test.py     # Database integration tests
```

## 🔒 Security Best Practices

- ✅ **Secrets never in code** - All sensitive data in environment variables
- ✅ **Environment separation** - Different configurations for dev/staging/production  
- ✅ **GitHub Secrets** - Encrypted secret storage for CI/CD
- ✅ **Container security** - Multi-stage Docker builds
- ✅ **CORS configuration** - Controlled cross-origin access

## 📈 Monitoring

The application includes comprehensive monitoring with Datadog:

- **APM Tracing** - Request/response tracking across all services
- **Runtime Metrics** - CPU, memory, and performance metrics
- **Custom Events** - Application-specific event tracking
- **Error Tracking** - Structured error logging and alerting
- **Test Visibility** - Test performance and flaky test detection

## 🚀 Deployment Architecture

- **Source**: GitHub repository
- **CI/CD**: GitHub Actions
- **Container Registry**: Docker Hub
- **Deployment Target**: Configurable (Synology NAS, cloud platforms)
- **Secrets Management**: GitHub Secrets
- **Monitoring**: Datadog APM and infrastructure monitoring

## 📚 API Documentation

When running locally, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Create a feature branch from `main`
2. Make your changes with appropriate tests
3. Ensure all tests pass: `pytest`
4. Submit a pull request with a clear description

## 📄 License

See [LICENSE.md](LICENSE.md) for license information.