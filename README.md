# FastAPI Image Processing & YouTube Summarization Service

A production-ready FastAPI application that combines intelligent image processing with AI-powered YouTube video summarization. Features comprehensive monitoring with Datadog integration, multi-database support (MongoDB, PostgreSQL, SQL Server), and flexible deployment options including Kubernetes and Synology NAS.

## 📋 Prerequisites

- Python 3.9 or higher
- Docker (optional, for containerized deployment)
- PostgreSQL, MongoDB, or SQL Server (at least one database)
- AWS Account (for S3, Rekognition, and SES)
- OpenAI API Key (for AI features)
- Datadog Account (optional, for monitoring)
- Notion Account (optional, for YouTube summaries storage)

## 🚀 Features

### **Image Processing & Storage**
- **AWS S3 Integration** - Secure image upload and storage
- **Amazon Rekognition** - Automated label detection, text extraction, and content moderation
- **Multi-Database Support** - Store metadata in MongoDB, PostgreSQL, or SQL Server
- **Content Safety** - Automatic detection of questionable content and "bug" images
- **Smart Error Detection** - Identifies images containing error text for debugging
- **Amazon SES Integration** - Email notifications for error reporting (replaced SendGrid)

### **YouTube Video Analysis**
- **AI-Powered Summarization** - Uses OpenAI to generate intelligent video summaries
- **Batch Processing** - Process multiple YouTube videos simultaneously with configurable strategies
- **Transcript Processing** - Extracts and processes YouTube video transcripts with fallback mechanisms
- **Notion Integration** - Automatically save video summaries to Notion databases
- **Metadata Extraction** - Retrieves video details including title, channel, and publication date
- **Multiple URL Support** - Accept various YouTube URL formats (standard, shorts, mobile)

### **Comprehensive Monitoring**
- **Datadog APM** - Full application performance monitoring with distributed tracing
- **LLM Observability** - Track AI model performance and costs
- **Custom Event Tracking** - Content moderation alerts, bug detection events
- **Runtime Profiling** - CPU and memory performance analysis
- **Health Monitoring** - Application health checks and uptime tracking

### **Production-Ready Architecture**
- **Docker Containerization** - Multi-stage builds with Python 3.9 slim base
- **Kubernetes Support** - Ready for container orchestration with manifest files
- **GitHub Actions CI/CD** - Automated testing, building, and deployment pipeline
- **Flexible Deployment** - Support for Docker, Kubernetes, Synology NAS, and cloud platforms
- **Environment Management** - Separate configurations for dev/staging/production
- **Database Migration Tools** - SQL scripts for easy database setup and schema management

## 📋 API Endpoints

### **Image Management**
- `GET /images?backend=mongo|postgres|sqlserver` - Retrieve all stored images
- `POST /add_image?backend=mongo|postgres|sqlserver` - Upload and process images
- `DELETE /delete_image/{id}?backend=mongo|postgres|sqlserver` - Remove images and metadata

### **AWS Services**
- `POST /api/v1/upload-image-amazon/` - Upload image directly to Amazon S3
- `DELETE /api/v1/delete-one-s3/{key}` - Delete single object from S3
- `DELETE /api/v1/delete-all-s3` - Delete all objects from S3

### **YouTube Processing**
- `POST /api/v1/summarize-youtube` - Generate AI summary of a single YouTube video
- `POST /api/v1/batch-summarize-youtube` - Process multiple YouTube videos with batch strategies
- `POST /api/v1/save-youtube-to-notion` - Save video summaries directly to Notion

### **OpenAI Services**
- `GET /api/v1/openai-hello` - Service health check
- `GET /api/v1/openai-gen-image/{prompt}` - Generate images using DALL-E 3

### **Database Operations**
- `GET /api/v1/mongo/get-image-mongo/{id}` - Retrieve image from MongoDB
- `DELETE /api/v1/mongo/delete-all-mongo/{key}` - Delete all items by key from MongoDB
- `GET /api/v1/postgres/get-image-postgres/{id}` - Retrieve image from PostgreSQL
- `GET /api/v1/sqlserver/get-image-sqlserver/{id}` - Retrieve image from SQL Server

### **Datadog Monitoring**
- `GET /datadog-hello` - Datadog integration health check
- `POST /datadog-event` - Send custom events to Datadog
- `GET /datadog-events` - Retrieve Datadog events
- `POST /app-event/{event_type}` - Track application-specific events
- `POST /track-api-request` - Log API request metrics
- `POST /bug-detection-event` - Report bug detection events

### **System & Monitoring**
- `GET /` - Root endpoint with welcome message
- `GET /health` - Application health status with detailed service checks
- `GET /test-sqlserver` - Test SQL Server connection
- `GET /timeout-test?timeout=N` - Performance testing endpoint
- `POST /create_post` - Demo endpoint for external API integration

## 🛠️ Quick Start

### **Local Development**

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd demo-fastapi
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your development credentials
   ```

4. **Set up databases (optional)**:
   ```bash
   # Interactive database setup
   ./scripts/setup-databases.sh
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8080`

### **Docker Development**

1. **Build and run with Docker**:
   ```bash
   # Basic build
   docker build -t fastapi-app .
   docker run -p 8080:8080 --env-file .env fastapi-app
   ```

2. **Using the build script**:
   ```bash
   # Local development with auto-run
   ./scripts/build.sh --local --run
   
   # Build without cache
   ./scripts/build.sh --no-cache --local --run
   
   # Clean existing containers and rebuild
   ./scripts/build.sh --clean --run
   ```

3. **Docker Compose**:
   ```bash
   docker-compose up
   ```

### **Alternative Container Runtimes**

```bash
# Using Podman
./scripts/build.sh --podman --run

# Using Rancher Desktop
./scripts/build.sh --rancher --run
```

## ⚙️ Configuration

### **Required Environment Variables**

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key

# AWS Services (S3, Rekognition, SES)
AMAZON_KEY_ID=your-aws-access-key-id
AMAZON_KEY_SECRET=your-aws-secret-access-key
AMAZON_S3_BUCKET=your-s3-bucket-name
SES_REGION=us-west-2
SES_FROM_EMAIL=your-verified-email@domain.com

# Database Configuration
# MongoDB (optional)
MONGO_CONN=mongodb://your-mongodb-connection
MONGO_USER=your-mongo-username
MONGO_PW=your-mongo-password

# PostgreSQL (optional)
PGHOST=your-postgres-host
PGPORT=5432
PGDATABASE=your-database-name
PGUSER=your-postgres-username
PGPASSWORD=your-postgres-password

# SQL Server (optional)
SQLSERVER_ENABLED=true  # Set to false to disable
SQLSERVERHOST=your-sqlserver-host
SQLSERVERPORT=1433
SQLSERVERDB=your-database-name
SQLSERVERUSER=your-sqlserver-username
SQLSERVERPW=your-sqlserver-password

# Notion Integration (optional)
NOTION_API_KEY=secret_your-notion-key
NOTION_DATABASE_ID=your-notion-database-id

# Datadog Monitoring
DD_API_KEY=your-datadog-api-key
DD_APP_KEY=your-datadog-app-key
DD_AGENT_HOST=192.168.1.100  # Your Datadog agent host
DD_TRACE_AGENT_PORT=8126
DD_PROFILING_ENABLED=true
DD_DBM_PROPAGATION_MODE=full  # Enable DB monitoring

# LLM Observability
DD_LLMOBS_ENABLED=true
DD_LLMOBS_ML_APP=youtube-summarizer
DD_LLMOBS_EVALUATORS=ragas_faithfulness,ragas_context_precision,ragas_answer_relevancy

# Application Configuration
DD_SERVICE=fastapi-app
DD_ENV=production
DD_VERSION=1.0
BUG_REPORT_EMAIL=your-email@domain.com
```

### **Optional Features**

The application gracefully handles missing services:
- **Databases**: MongoDB, PostgreSQL, and SQL Server can be used independently or together
- **Notion Integration**: YouTube summaries work without Notion
- **Datadog**: Monitoring is optional for development
- **Amazon SES**: Email notifications are optional (fallback available)

## 🐳 Docker Configuration

### **Dockerfile Features**
- **Multi-stage build** for optimal image size
- **Python 3.9 slim** base image
- **Security hardening** with non-root user (PUID/PGID)
- **Environment optimization** for container runtime
- **Health checks** for container orchestration

### **Build Options**
```bash
# Standard build for production
docker build -t fastapi-app .

# Platform-specific builds
docker build --platform linux/amd64 -t fastapi-app .

# No-cache build
docker build --no-cache -t fastapi-app .
```

### **Synology NAS Deployment**
```bash
# Build image for Synology DS923+
./scripts/build.sh

# This creates a .tar file on your Desktop for import into Synology Container Manager
# Port mapping: 9000:8080
# Environment: Use .env.production values
```

## 💡 Usage Examples

### **Batch YouTube Processing**
```python
# See examples/youtube_batch_usage.py for complete examples
import asyncio
from examples.youtube_batch_usage import YouTubeBatchClient

async def batch_process_videos():
    client = YouTubeBatchClient()
    
    # Process multiple videos
    urls = [
        "https://youtube.com/watch?v=video1",
        "https://youtube.com/watch?v=video2",
        "https://youtube.com/watch?v=video3"
    ]
    
    result = await client.process_batch(
        urls=urls,
        strategy="parallel_individual",
        save_to_notion=True,
        max_parallel=3
    )
    
    print(f"Processed {len(result['results'])} videos")

asyncio.run(batch_process_videos())
```

### **Database Setup**
```bash
# Interactive database setup wizard
./scripts/setup-databases.sh

# Quick PostgreSQL setup
psql -h localhost -U username -d database_name -f sql/quick_setup_postgres.sql

# Fix and setup PostgreSQL
psql -h localhost -U username -d database_name -f sql/fix_and_setup_postgres.sql

# SQL Server setup
sqlcmd -S localhost -U sa -d database_name -i sql/sqlserver_schema.sql
```

### **Secret Management**
```bash
# Set up GitHub Secrets for CI/CD
./scripts/setup-secrets.sh

# Clear sensitive environment variables
./scripts/clear-secrets.sh
```

## 🧪 Testing

### **Run Tests**
```bash
# All tests
pytest

# With coverage
pytest --cov=src

# Specific test files
pytest tests/test_basic.py
pytest tests/test_simple.py
pytest tests/mongo_test.py

# Run test script
./scripts/test.sh
```

### **YouTube URL Testing**
```bash
# Test YouTube URL processing and transcript retrieval
python test_youtube_urls.py
```
This utility tests:
- Video ID extraction from different URL formats
- Transcript retrieval functionality
- Full video processing pipeline

### **Test Environment**
Tests are designed to gracefully handle missing external services:
- **Mock external APIs** when credentials are unavailable
- **Skip integration tests** for unconfigured services
- **Isolated unit tests** for core functionality

## 📁 Project Structure

```
demo-fastapi/
├── main.py                     # FastAPI application with Datadog integration
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Multi-stage container build
├── docker-compose.yml          # Local development services
├── env.example                 # Environment variable template
├── pytest.ini                # Test configuration
├── scripts/                   # Build and deployment automation
│   ├── build.sh              # Multi-platform Docker builds
│   ├── deploy.sh             # Production deployment
│   ├── setup-secrets.sh      # GitHub Secrets management
│   ├── setup-databases.sh    # Database setup and migration helper
│   └── test.sh               # Test automation
├── src/                       # Application modules
│   ├── amazon.py             # AWS S3, Rekognition, SES integration
│   ├── mongo.py              # MongoDB operations
│   ├── postgres.py           # PostgreSQL operations
│   ├── sqlserver.py          # SQL Server operations
│   ├── openai_service.py     # OpenAI API integration
│   ├── datadog.py            # Custom monitoring and events
│   └── services/             # Additional service integrations
│       ├── youtube_service.py          # Single video processing
│       ├── youtube_batch_service.py    # Batch video processing
│       ├── youtube_transcript_fallback.py # Transcript fallback handling
│       └── notion_service.py           # Notion database integration
├── tests/                     # Test suite
│   ├── conftest.py           # Test configuration and fixtures
│   ├── test_basic.py         # API endpoint tests
│   ├── test_simple.py        # Unit tests
│   └── mongo_test.py         # Database integration tests
├── sql/                       # Database schemas and migrations
│   ├── postgres_schema.sql   # PostgreSQL table definitions
│   ├── sqlserver_schema.sql  # SQL Server table definitions
│   └── *.sql                 # Migration and setup scripts
├── examples/                  # Usage examples
│   └── youtube_batch_usage.py # Batch processing examples
├── docs/                      # Additional documentation
│   ├── GMKTEC_MIGRATION.md   # GMKTec host migration guide
│   ├── SQL_SERVER_SETUP.md   # SQL Server configuration guide
│   └── YOUTUBE_BATCH_PROCESSING.md # YouTube batch processing guide
├── .github/workflows/         # CI/CD pipelines
│   ├── deploy.yaml           # Main deployment workflow
│   └── datadog-security.yml  # Datadog security scanning
├── k8s-fastapi-app.yaml      # Kubernetes application manifest
├── k8s-datadog-agent.yaml    # Kubernetes Datadog agent manifest
├── test_youtube_urls.py      # YouTube URL processing test utility
├── static-analysis.datadog.yml # Datadog static analysis configuration
└── tailscale-acl-example.json # Tailscale ACL configuration example
```

## 🔍 Key Application Features

### **Image Processing Workflow**
1. **Upload** - Images uploaded to AWS S3
2. **Analysis** - Amazon Rekognition extracts labels, text, and checks content
3. **Storage** - Metadata stored in MongoDB, PostgreSQL, or SQL Server
4. **Monitoring** - Content moderation and error detection events sent to Datadog

### **YouTube Processing Workflow**
1. **URL Parsing** - Extract video ID from multiple YouTube URL formats
2. **Transcript Retrieval** - Get video transcript with multiple fallback mechanisms
3. **AI Summarization** - Generate summary using OpenAI GPT with custom instructions
4. **Batch Processing** - Handle multiple videos with configurable parallel processing strategies
5. **Optional Storage** - Save to Notion database with metadata and tags

### **Monitoring & Observability**
- **Request Tracing** - Every API call tracked with Datadog APM
- **Error Detection** - Custom events for content moderation and bug detection
- **Performance Metrics** - CPU, memory, and response time monitoring
- **LLM Observability** - OpenAI usage tracking with RAGAS evaluators for model quality assessment
- **Database Monitoring** - APM trace correlation with database queries (DBM)
- **Runtime Profiling** - CPU and memory profiling for performance optimization
- **Custom Events API** - Send application-specific events to Datadog
- **Static Analysis** - Code quality checks with Datadog's rulesets

## 🚀 Deployment Options

### **Docker (Local/Cloud)**
```bash
docker run -p 8080:8080 --env-file .env fastapi-app
```

### **Kubernetes**
```bash
kubectl apply -f k8s-fastapi-app.yaml
kubectl apply -f k8s-datadog-agent.yaml
```

### **Synology NAS**
1. Build image: `./scripts/build.sh`
2. Transfer .tar file to Synology
3. Import via Container Manager
4. Configure port 9000:8080

### **GitHub Actions CI/CD**
The repository includes comprehensive CI/CD pipelines:
- **Main Deployment** (`.github/workflows/deploy.yaml`) - Automated build and deployment with Tailscale integration
- **Security Scanning** (`.github/workflows/datadog-security.yml`) - Static analysis and security checks

### **GMKTec Host Deployment**
Deploy to GMKTec host via Tailscale network:
```bash
# Using the deployment script
./scripts/deploy.sh --gmktec

# Enterprise setup
./scripts/enterprise-setup.sh
```

## 📊 Monitoring Dashboard

Access your monitoring dashboards:
- **Datadog APM**: Distributed tracing and performance metrics
- **Datadog LLM Observability**: Track AI model performance and costs
- **FastAPI Docs**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`
- **Health Check**: `http://localhost:8080/health`

## 📖 Additional Documentation

Detailed guides are available in the `docs/` directory:
- **[GMKTec Migration Guide](docs/GMKTEC_MIGRATION.md)** - Detailed instructions for migrating to GMKTec host
- **[SQL Server Setup Guide](docs/SQL_SERVER_SETUP.md)** - Complete SQL Server configuration and troubleshooting
- **[YouTube Batch Processing Guide](docs/YOUTUBE_BATCH_PROCESSING.md)** - Advanced YouTube video processing strategies

## 🔒 Security Features

- **Environment Variable Management** - No secrets in code, comprehensive `.env` configuration
- **CORS Configuration** - Controlled cross-origin access with configurable origins
- **Content Moderation** - Automatic detection of inappropriate content using Amazon Rekognition
- **Error Tracking** - Structured logging with Datadog integration for security monitoring
- **Container Security** - Non-root user execution with PUID/PGID support
- **Static Security Analysis** - Automated security scanning with Datadog's Python security rulesets
- **Tailscale Integration** - Secure network access for deployments
- **OAuth Integration** - Secure authentication for CI/CD pipelines

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

See [LICENSE.md](LICENSE.md) for license information.