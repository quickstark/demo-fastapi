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

#### `setup-secrets.sh` - GitHub Secrets Management
```bash
# Upload secrets from environment file
./scripts/setup-secrets.sh .env.production
```

**Requirements:**
- GitHub CLI (`gh`) must be installed and authenticated
- Valid environment file with actual values (not placeholders)

**Features:**
- Automatically skips `SYNOLOGY_SSH_KEY` to prevent corruption
- Validates API key formats and provides troubleshooting guidance
- Shows detailed progress and skipped variables

#### `validate-ses.sh` - Amazon SES Email Configuration Validation
```bash
# Validate SES configuration and connectivity
./scripts/validate-ses.sh .env.production
```

**Requirements:**
- AWS credentials (AMAZON_KEY_ID/AMAZON_KEY_SECRET) in environment file
- Python3 and/or AWS CLI for comprehensive testing

**Features:**
- Validates AWS credentials and SES configuration
- Tests SES API connectivity and permissions
- Checks sender email verification status
- Verifies sandbox mode status
- Validates GitHub Secrets configuration

#### `clear-secrets.sh` - GitHub Secrets Cleanup
```bash
# Interactive cleanup
./scripts/clear-secrets.sh

# Dry run to see what would be deleted
./scripts/clear-secrets.sh --dry-run

# Delete all secrets (with confirmation)
./scripts/clear-secrets.sh --all

# Keep specific secrets
./scripts/clear-secrets.sh --exclude DD_API_KEY,DD_APP_KEY

# Delete only Synology-related secrets
./scripts/clear-secrets.sh --pattern '^SYNOLOGY_'
```

**Features:**
- Interactive or bulk deletion modes
- Dry-run capability to preview changes
- Pattern matching for selective deletion
- Exclude list to preserve important secrets
- Grouped display by category (Database, AWS, Datadog, etc.)
- Multiple safety confirmations

**Use Cases:**
- Clean slate for migrations (e.g., Synology to GMKTec)
- Remove obsolete secrets after infrastructure changes
- Selective cleanup of specific secret categories

### Deployment & Infrastructure Scripts

#### `setup-gmktec-migration.sh` - GMKTec Host Migration Setup
```bash
# Set up SSH keys and prepare for GMKTec migration
./scripts/setup-gmktec-migration.sh
```

**Features:**
- Generates SSH key pair for GitHub Actions
- Tests SSH connectivity to GMKTec host
- Displays GitHub Secrets configuration
- Provides Tailscale OAuth setup instructions
- Lists database configuration updates needed
- Step-by-step migration guidance

**Use with:**
- `clear-secrets.sh` to remove old Synology secrets
- `setup-secrets.sh` to upload new GMKTec configuration
- See `docs/GMKTEC_MIGRATION.md` for complete migration guide

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
- `DD_API_KEY` - Datadog API key
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

### Infrastructure Migration Workflow (e.g., Synology to GMKTec)
```bash
# 1. Clean up old secrets
./scripts/clear-secrets.sh --dry-run  # Preview what will be deleted
./scripts/clear-secrets.sh --pattern '^SYNOLOGY_'  # Remove old infra secrets

# 2. Set up new infrastructure
./scripts/setup-gmktec-migration.sh  # Generate SSH keys and get instructions

# 3. Update environment file with new values
# Edit .env.production with new database hosts, ports, etc.

# 4. Upload new secrets
./scripts/setup-secrets.sh .env.production

# 5. Deploy to new infrastructure
git add .github/workflows/deploy.yaml
git commit -m "feat: migrate to GMKTec infrastructure"
git push
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
├── setup-secrets.sh          # GitHub secrets upload
├── clear-secrets.sh          # GitHub secrets cleanup
├── setup-gmktec-migration.sh # GMKTec migration helper
├── validate-ses.sh           # Amazon SES validation
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

**Amazon SES Email Delivery Issues:**
- **AWS Credentials**: Verify `AMAZON_KEY_ID` and `AMAZON_KEY_SECRET` are correct and have SES permissions
- **Sender Verification**: Ensure your sender email is verified in AWS SES console
- **Sandbox Mode**: Check if your SES account is in sandbox mode (only verified emails can receive messages)
- **Region Configuration**: Verify `SES_REGION` matches where your sender email is verified
- **Send Quota**: Check if you've exceeded your daily sending quota or sending rate

**Environment Variables**: 
- Verify SES configuration is properly set in your `.env.production` file:
  ```bash
  SES_REGION=us-east-1
  SES_FROM_EMAIL=your-verified-email@domain.com
  AMAZON_KEY_ID=your-aws-access-key
  AMAZON_KEY_SECRET=your-aws-secret-key
  ```
- Check that secrets are uploaded to GitHub: `gh secret list | grep -E "(SES_|AMAZON_)"`

**Testing**: Test your SES configuration:
```bash
# Run the validation script
./scripts/validate-ses.sh .env.production

# Or test with AWS CLI directly
aws ses send-email --region us-east-1 \
    --source "your-email@domain.com" \
    --destination "ToAddresses=test@example.com" \
    --message "Subject={Data=Test},Body={Text={Data=Test}}"
```

**SYNOLOGY_SSH_KEY Issues:**
- The `setup-secrets.sh` script now automatically skips `SYNOLOGY_SSH_KEY` to prevent corruption
- Manually manage this secret in GitHub repository settings
- Ensure the SSH key format is preserved (including line breaks) 