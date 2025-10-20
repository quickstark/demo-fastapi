# Deployment Workflows Guide

## Available Workflows

Your FastAPI application has **three** deployment workflows configured:

### 1. **Self-Hosted Runner Deployment** (Recommended)
- **File**: `.github/workflows/deploy-self-hosted.yaml`
- **Trigger**: Push to `main` branch or manual dispatch
- **Runner**: Your self-hosted GitHub runner on GMKTec
- **Port**: 9000

**Features:**
- ✅ SonarQube code analysis using Docker
- ✅ Automated testing in containers
- ✅ Docker image build and push to Docker Hub
- ✅ Local deployment on the same machine
- ✅ Health checks and validation
- ✅ Datadog deployment marking

**Use when:** Deploying to your local GMKTec machine with full control

### 2. **GitHub-Hosted Deployment** 
- **File**: `.github/workflows/deploy.yaml`
- **Trigger**: Manual dispatch only
- **Runner**: GitHub-hosted runners
- **Port**: Configurable

**Features:**
- ✅ Complete CI/CD pipeline with all checks
- ✅ Multiple Python version testing
- ✅ SonarQube analysis
- ✅ Security scanning with Datadog
- ✅ Remote deployment via Tailscale

**Use when:** Deploying from GitHub's infrastructure to remote servers

### 3. **Datadog Security Scanning**
- **File**: `.github/workflows/datadog-security.yml`
- **Trigger**: Push to any branch
- **Runner**: GitHub-hosted
- **Purpose**: Security analysis only

**Features:**
- ✅ Automated security scanning
- ✅ Static code analysis
- ✅ Vulnerability detection
- ✅ No deployment (analysis only)

## Consolidated Changes

### What Was Changed

Previously, there were **two** self-hosted deployment workflows:
1. `deploy-self-hosted.yaml` - Used SonarSource GitHub action (required installing dependencies)
2. `deploy-self-hosted-alternative.yaml` - Incomplete, used Docker for SonarQube

**Consolidation:**
- ✅ Merged into single `deploy-self-hosted.yaml`
- ✅ Uses Docker for SonarQube (cleaner, no host dependencies)
- ✅ Added `SQLSERVER_ENABLED` environment variable
- ✅ Removed redundant dependency installation steps
- ✅ Deleted incomplete alternative workflow

### SonarQube Implementation

**Before:**
```yaml
# Required installing unzip on host
- name: Install SonarQube Dependencies
  run: sudo apt-get install -y unzip

- name: SonarQube Scan
  uses: SonarSource/sonarqube-scan-action@v6
```

**After:**
```yaml
# Uses Docker - no host dependencies needed
- name: SonarQube Scan
  run: |
    docker run --rm \
      -e SONAR_HOST_URL="${{ secrets.SONAR_HOST_URL }}" \
      -e SONAR_TOKEN="${{ secrets.SONAR_TOKEN }}" \
      -v "$(pwd):/usr/src" \
      sonarsource/sonar-scanner-cli \
      -Dsonar.projectKey=quickstark_demo-fastapi_... \
      -Dsonar.sources=main.py,src \
      -Dsonar.tests=tests
```

### SQL Server Toggle Integration

Added support for the SQL Server environment toggle:

```yaml
-e SQLSERVER_ENABLED="${{ secrets.SQLSERVER_ENABLED || 'true' }}" \
-e SQLSERVERHOST="${{ secrets.SQLSERVERHOST }}" \
-e SQLSERVERPORT="${{ secrets.SQLSERVERPORT }}" \
```

## Using the Workflows

### Self-Hosted Deployment (GMKTec)

**Automatic:**
```bash
# Simply push to main
git push origin main

# Workflow automatically:
# 1. Runs SonarQube analysis
# 2. Runs tests
# 3. Builds Docker image
# 4. Deploys to port 9000
```

**Manual:**
```bash
# Go to GitHub Actions
# Select "Build and Deploy (Self-Hosted Runner)"
# Click "Run workflow"
# Options:
#   - Skip tests: true/false
#   - Skip deployment: true/false (build only)
```

### GitHub-Hosted Deployment

**Manual Only:**
```bash
# Go to GitHub Actions
# Select "Deploy FastAPI to Production (GitHub-Hosted)"
# Click "Run workflow"
# Requires:
#   - TAILSCALE_OAUTH_CLIENT_ID
#   - TAILSCALE_OAUTH_CLIENT_SECRET
#   - GMKTEC_HOST
#   - SSH_PRIVATE_KEY
```

## Required GitHub Secrets

### For Self-Hosted Runner

**Core Secrets:**
```bash
# Docker Hub
DOCKERHUB_USER=your-username
DOCKERHUB_TOKEN=your-token

# Datadog
DD_SERVICE=fastapi-app
DD_ENV=production
DD_API_KEY=your-datadog-api-key
DD_APP_KEY=your-datadog-app-key
DD_AGENT_HOST=192.168.1.200

# PostgreSQL
PGHOST=192.168.1.200
PGPORT=9001
PGDATABASE=images
PGUSER=postgres
PGPASSWORD=your-password

# SQL Server (Optional - can be toggled)
SQLSERVER_ENABLED=true  # Set to 'false' to disable
SQLSERVERHOST=192.168.1.200
SQLSERVERPORT=9002
SQLSERVERUSER=sa
SQLSERVERPW=Pass@word123
SQLSERVERDB=images

# AWS
AMAZON_KEY_ID=your-aws-key
AMAZON_KEY_SECRET=your-aws-secret
AMAZON_S3_BUCKET=your-bucket
SES_REGION=us-west-2
SES_FROM_EMAIL=your-email@domain.com

# OpenAI
OPENAI_API_KEY=sk-your-key

# MongoDB (Optional)
MONGO_CONN=mongodb://your-connection
MONGO_USER=your-user
MONGO_PW=your-password

# Notion (Optional)
NOTION_API_KEY=secret_your-key
NOTION_DATABASE_ID=your-database-id

# SonarQube (Optional)
SONAR_TOKEN=your-sonarqube-token
SONAR_HOST_URL=https://your-sonarqube-server.com

# Other
BUG_REPORT_EMAIL=your-email@domain.com
```

## Workflow Steps Breakdown

### Self-Hosted Workflow Steps

1. **Checkout Code** - Fetch repository with full history
2. **SonarQube Scan** - Code quality analysis in Docker
3. **System Information** - Display runner environment
4. **Check Available Tools** - Verify Docker, Python, curl, etc.
5. **Setup Python** - Create venv if Python available
6. **Run Tests** - Execute pytest (in Docker or local Python)
7. **Build Docker Image** - Build and tag application image
8. **Push to Docker Hub** - Upload image for deployment
9. **Deploy to Local Docker** - Run container on port 9000
10. **Health Check** - Verify application is running
11. **Deployment Notification** - Report success/failure
12. **Mark in Datadog** - Optional deployment tracking

## Toggling SQL Server in Deployment

### Enable SQL Server
```bash
# In GitHub Secrets, set:
SQLSERVER_ENABLED=true
SQLSERVERHOST=192.168.1.200
SQLSERVERPORT=9002
# ... other SQL Server variables
```

### Disable SQL Server
```bash
# In GitHub Secrets, set:
SQLSERVER_ENABLED=false
# SQL Server variables can remain but won't be used
```

**Benefits of Disabling:**
- ⚡ Faster application startup (no connection wait)
- 🚀 Reduced deployment time
- 🔧 Easier testing without SQL Server dependency

## Monitoring Deployments

### View Logs
```bash
# On GMKTec machine
docker logs -f images-api

# Check last 100 lines
docker logs --tail 100 images-api
```

### Check Health
```bash
# Health endpoint
curl http://localhost:9000/health

# Database status
curl http://localhost:9000/api/v1/database-status

# Root endpoint
curl http://localhost:9000/
```

### Datadog Monitoring
- Deployments are automatically marked in Datadog
- View in Datadog APM → Deployments
- Track version changes and performance

## Troubleshooting

### Workflow Fails at SonarQube
```bash
# Check if SonarQube is accessible
curl $SONAR_HOST_URL

# Verify secrets are set
# Go to GitHub → Settings → Secrets → Actions
# Check SONAR_TOKEN and SONAR_HOST_URL

# SonarQube failure doesn't stop deployment (continue-on-error: true)
```

### Workflow Fails at Docker Build
```bash
# On GMKTec, check Docker
docker ps
docker version

# Check Docker socket access
ls -la /var/run/docker.sock

# Restart Docker if needed
sudo systemctl restart docker
```

### Workflow Fails at Deployment
```bash
# Check if port 9000 is available
sudo lsof -i :9000

# Stop existing container
docker stop images-api
docker rm images-api

# Check Docker Hub credentials
echo $DOCKERHUB_TOKEN | docker login --username $DOCKERHUB_USER --password-stdin
```

### Health Check Fails
```bash
# Check container is running
docker ps | grep images-api

# Check container logs
docker logs --tail 50 images-api

# Check if databases are accessible
curl http://localhost:9000/api/v1/database-status

# Test SQL Server specifically
curl http://localhost:9000/test-sqlserver
```

## Best Practices

### Development Workflow
1. Work on feature branch
2. Push to feature branch (triggers security scan only)
3. Create PR to main
4. After PR review, merge to main
5. Automatic deployment to GMKTec

### Production Deployment
1. Ensure all tests pass
2. Verify SonarQube quality gate
3. Check database connectivity before deployment
4. Monitor Datadog during deployment
5. Verify health endpoints after deployment

### SQL Server Management
1. Start with `SQLSERVER_ENABLED=false` for faster iterations
2. Enable SQL Server when needed for production features
3. Use database status endpoint to verify connectivity
4. Toggle as needed without code changes

## Summary

**One Deployment Workflow** = Cleaner, Simpler, Better
- ✅ Single source of truth for self-hosted deployments
- ✅ Docker-based SonarQube (no host dependencies)
- ✅ SQL Server toggle support
- ✅ Comprehensive health checks
- ✅ Automatic deployment on push to main

**Three Total Workflows:**
1. **Self-Hosted** - Main deployment workflow (this machine)
2. **GitHub-Hosted** - Remote deployment via Tailscale
3. **Security Scan** - Automated security analysis only
