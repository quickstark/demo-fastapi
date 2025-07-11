# FastAPI Image Processing & YouTube Summarization Service

A production-ready FastAPI application that combines intelligent image processing with AI-powered YouTube video summarization. Features comprehensive monitoring, multi-database support, and flexible deployment options.

## 🚀 Features

### **Image Processing & Storage**
- **AWS S3 Integration** - Secure image upload and storage
- **Amazon Rekognition** - Automated label detection, text extraction, and content moderation
- **Multi-Database Support** - Store metadata in MongoDB or PostgreSQL
- **Content Safety** - Automatic detection of questionable content and "bug" images
- **Smart Error Detection** - Identifies images containing error text for debugging

### **YouTube Video Analysis**
- **AI-Powered Summarization** - Uses OpenAI to generate intelligent video summaries
- **Transcript Processing** - Extracts and processes YouTube video transcripts
- **Notion Integration** - Automatically save video summaries to Notion databases
- **Metadata Extraction** - Retrieves video details including title, channel, and publication date

### **Comprehensive Monitoring**
- **Datadog APM** - Full application performance monitoring with distributed tracing
- **LLM Observability** - Track AI model performance and costs
- **Custom Event Tracking** - Content moderation alerts, bug detection events
- **Runtime Profiling** - CPU and memory performance analysis
- **Health Monitoring** - Application health checks and uptime tracking

### **Production-Ready Architecture**
- **Docker Containerization** - Multi-stage builds for optimal performance
- **Kubernetes Support** - Ready for container orchestration
- **Flexible Deployment** - Support for Docker, Kubernetes, and Synology NAS
- **Environment Management** - Separate configurations for dev/staging/production

## 📋 API Endpoints

### **Image Management**
- `GET /images?backend=mongo|postgres` - Retrieve all stored images
- `POST /add_image?backend=mongo|postgres` - Upload and process images
- `DELETE /delete_image/{id}?backend=mongo|postgres` - Remove images and metadata

### **YouTube Processing**
- `POST /api/v1/summarize-youtube` - Generate AI summaries of YouTube videos
- `POST /api/v1/save-youtube-to-notion` - Save video summaries directly to Notion

### **OpenAI Services**
- `GET /api/v1/openai-hello` - Service health check
- `GET /api/v1/openai-gen-image/{prompt}` - Generate images using DALL-E 3

### **Database Operations**
- `GET /api/v1/mongo/*` - MongoDB operations and testing
- `GET /api/v1/postgres/*` - PostgreSQL operations and testing

### **System & Monitoring**
- `GET /` - Root endpoint with welcome message
- `GET /health` - Application health status
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

4. **Run the application**:
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

# Notion Integration (optional)
NOTION_API_KEY=secret_your-notion-key
NOTION_DATABASE_ID=your-notion-database-id

# Datadog Monitoring
DATADOG_API_KEY=your-datadog-api-key
DATADOG_APP_KEY=your-datadog-app-key
DD_AGENT_HOST=192.168.1.100  # Your Datadog agent host
DD_TRACE_AGENT_PORT=8126

# Application Configuration
DD_SERVICE=fastapi-app
DD_ENV=production
DD_VERSION=1.0
BUG_REPORT_EMAIL=your-email@domain.com
```

### **Optional Features**

The application gracefully handles missing services:
- **MongoDB/PostgreSQL**: Either database can be used, or both
- **Notion Integration**: YouTube summaries work without Notion
- **Datadog**: Monitoring is optional for development

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

## 🧪 Testing

### **Run Tests**
```bash
# All tests
pytest

# With coverage
pytest --cov=src

# Specific test files
pytest tests/test_basic.py
pytest tests/mongo_test.py
```

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
│   └── test.sh               # Test automation
├── src/                       # Application modules
│   ├── amazon.py             # AWS S3, Rekognition, SES integration
│   ├── mongo.py              # MongoDB operations
│   ├── postgres.py           # PostgreSQL operations
│   ├── openai_service.py     # OpenAI API integration
│   ├── datadog.py            # Custom monitoring and events
│   └── services/             # Additional service integrations
│       ├── youtube_service.py # YouTube transcript processing
│       └── notion_service.py  # Notion database integration
├── tests/                     # Test suite
│   ├── conftest.py           # Test configuration and fixtures
│   ├── test_basic.py         # API endpoint tests
│   ├── test_simple.py        # Unit tests
│   └── mongo_test.py         # Database integration tests
└── k8s-*.yaml                # Kubernetes deployment manifests
```

## 🔍 Key Application Features

### **Image Processing Workflow**
1. **Upload** - Images uploaded to AWS S3
2. **Analysis** - Amazon Rekognition extracts labels, text, and checks content
3. **Storage** - Metadata stored in MongoDB or PostgreSQL
4. **Monitoring** - Content moderation and error detection events sent to Datadog

### **YouTube Processing Workflow**
1. **URL Parsing** - Extract video ID from YouTube URL
2. **Transcript Retrieval** - Get video transcript using YouTube API
3. **AI Summarization** - Generate summary using OpenAI GPT
4. **Optional Storage** - Save to Notion database with metadata

### **Monitoring & Observability**
- **Request Tracing** - Every API call tracked with Datadog APM
- **Error Detection** - Custom events for content moderation and bug detection
- **Performance Metrics** - CPU, memory, and response time monitoring
- **LLM Tracking** - OpenAI usage and performance metrics

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

## 📊 Monitoring Dashboard

Access your monitoring dashboards:
- **Datadog APM**: Distributed tracing and performance metrics
- **FastAPI Docs**: `http://localhost:8080/docs`
- **Health Check**: `http://localhost:8080/health`

## 🔒 Security Features

- **Environment Variable Management** - No secrets in code
- **CORS Configuration** - Controlled cross-origin access
- **Content Moderation** - Automatic detection of inappropriate content
- **Error Tracking** - Structured logging for security monitoring
- **Container Security** - Non-root user execution

## 📚 API Documentation

When running locally, interactive API documentation is available:
- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

See [LICENSE.md](LICENSE.md) for license information.