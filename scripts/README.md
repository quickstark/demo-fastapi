# Scripts Directory

This directory contains all project automation scripts organized for clarity and maintainability.

## Script Overview

### Core Development Scripts

#### `build.sh` - Docker Build & Test
```bash
# Build for local development
./scripts/build.sh --local --run

# Build for Synology NAS
./scripts/build.sh

# Build with specific options
./scripts/build.sh --no-cache --clean --podman
```

**Options:**
- `--local` - Build for local testing
- `--run` - Start container after build (implies --local)
- `--clean` - Remove existing containers
- `--no-cache` - Build without Docker cache
- `--podman` - Use Podman instead of Docker
- `--rancher` - Use Rancher Desktop with nerdctl

#### `test.sh` - Test Runner with Datadog Integration
```bash
# Run all tests
./scripts/test.sh

# Run specific test types
./scripts/test.sh unit -v
./scripts/test.sh integration --cov=src
./scripts/test.sh fast
./scripts/test.sh mongo
```

**Test Types:**
- `unit` - Unit tests only
- `integration` - Integration tests only
- `fast` - Excludes slow and mongo tests
- `mongo` - MongoDB tests only
- `no-mongo` - All tests except MongoDB
- `all` - All tests (default)

### Deployment & Infrastructure Scripts

#### `deploy.sh` - Production Deployment
```bash
# Deploy with default environment file
./scripts/deploy.sh

# Deploy with specific environment file
./scripts/deploy.sh .env.staging
```

**Features:**
- Environment validation
- Git operations (commit, push)
- GitHub secrets upload
- Deployment monitoring
- Post-deployment guidance

#### `setup-secrets.sh` - GitHub Secrets Management
```bash
# Upload secrets from environment file
./scripts/setup-secrets.sh .env.production
```

**Requirements:**
- GitHub CLI (`gh`) must be installed and authenticated
- Valid environment file with actual values (not placeholders)

#### `enterprise-setup.sh` - Enterprise CI/CD Features
```bash
# Set up specific features
./scripts/enterprise-setup.sh security
./scripts/enterprise-setup.sh monitoring
./scripts/enterprise-setup.sh iac

# Interactive setup
./scripts/enterprise-setup.sh
```

**Features:**
- Security scanning (SAST, container security)
- Comprehensive testing (unit, integration, performance)
- Advanced monitoring (Prometheus, Grafana)
- Infrastructure as Code (Terraform)
- Compliance & governance (OPA policies)

## Script Dependencies

### Required Tools
- **Docker/Podman** - For container operations
- **GitHub CLI** (`gh`) - For secrets management and deployment
- **Python 3.11+** - For test execution
- **Git** - For version control operations

### Optional Tools
- **Rancher Desktop** - Alternative container runtime
- **Terraform** - For IaC features
- **K6** - For performance testing

## Environment Variables

### Datadog Configuration
- `DD_API_KEY` / `DATADOG_API_KEY` - Datadog API key
- `DD_ENV` - Environment name (test, staging, prod)
- `DD_SERVICE` - Service name
- `DD_VERSION` - Version identifier

### GitHub Integration
- `GITHUB_TOKEN` - GitHub Personal Access Token (for setup-secrets.sh)

### Database Configuration
- `MONGO_CONN` - MongoDB connection string
- `MONGO_USER` - MongoDB username
- `MONGO_PW` - MongoDB password
- `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` - PostgreSQL config

## Usage Examples

### Local Development Workflow
```bash
# 1. Build and test locally
./scripts/build.sh --local --run

# 2. Run tests
./scripts/test.sh fast

# 3. Full test suite before deployment
./scripts/test.sh all --cov=src
```

### Production Deployment Workflow
```bash
# 1. Prepare environment file
cp env.example .env.production
# Edit .env.production with actual values

# 2. Deploy to production
./scripts/deploy.sh .env.production
```

### CI/CD Enhancement Workflow
```bash
# 1. Add security scanning
./scripts/enterprise-setup.sh security

# 2. Set up monitoring
./scripts/enterprise-setup.sh monitoring

# 3. Add all enterprise features
./scripts/enterprise-setup.sh
```

## File Organization

```
scripts/
├── README.md                 # This documentation
├── build.sh                  # Docker build & container management
├── test.sh                   # Test runner with Datadog integration
├── deploy.sh                 # Production deployment workflow
├── setup-secrets.sh          # GitHub secrets management
└── enterprise-setup.sh       # Enterprise CI/CD features
```

## Migration Notes

### From Previous Structure
- `build.sh` moved from root to `scripts/build.sh`
- `run_tests.sh` renamed to `scripts/test.sh` with improvements
- `scripts/setup_secrets.py` removed (redundant with bash version)
- `scripts/requirements.txt` removed (merged with main requirements)

### Path Updates Required
If you have any automation that references the old paths:
- `./build.sh` → `./scripts/build.sh`
- `./run_tests.sh` → `./scripts/test.sh`

## Troubleshooting

### Common Issues

**Docker Build Fails:**
- Ensure Docker is running
- Try `--no-cache` flag
- Check disk space

**Tests Fail to Start:**
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version`
- Verify environment variables

**GitHub Secrets Upload Fails:**
- Authenticate with GitHub CLI: `gh auth login`
- Check repository permissions
- Verify environment file format

**Deployment Issues:**
- Check GitHub Actions logs
- Verify all secrets are set correctly
- Ensure SSH key has proper permissions 