# Production Deployment Guide

## Environment Variable Management Strategy

This project follows production-level best practices for environment variable management across different deployment environments.

## 🏗️ Architecture Overview

### **1. Multi-Environment Strategy**
- **Development**: Local `.env` files (not committed)
- **Production**: GitHub Secrets → Container Environment Variables
- **Staging**: Separate secret sets for staging environment

### **2. Security Layers**
- ✅ **Secrets never in code**: All sensitive data in GitHub Secrets
- ✅ **Environment separation**: Different secrets for dev/staging/prod
- ✅ **Principle of least privilege**: Only necessary secrets exposed
- ✅ **Audit trail**: GitHub tracks secret access and changes

## 🚀 Quick Start: One-Command Deployment

### **Recommended: Use the Comprehensive Deploy Script**

For the fastest and most reliable deployment, use our all-in-one deploy script:

```bash
# Make sure you have a .env.production file with your actual values
cp env.example .env.production
# Edit .env.production with your real values

# Run the comprehensive deployment script
./scripts/deploy.sh .env.production
```

**What this script does:**
- ✅ **Validates prerequisites** (Git, GitHub CLI, authentication)
- ✅ **Validates environment file** (checks for placeholders, empty values)
- ✅ **Handles git operations** (add, commit, push with prompts)
- ✅ **Uploads all secrets** to GitHub automatically
- ✅ **Monitors deployment** progress and provides links
- ✅ **Provides post-deployment guidance** and troubleshooting tips

**Interactive prompts guide you through:**
- Selecting environment files
- Reviewing changes before commit
- Customizing commit messages
- Watching deployment progress

This approach combines the convenience of automation with the safety of human oversight at critical steps.

---

## 🔧 Alternative Setup Methods

If you prefer more granular control or are setting up CI/CD infrastructure, choose one of these approaches:

### **Step 1: Choose Your Secret Management Approach**

Instead of manually setting GitHub Secrets, choose one of these automated approaches:

#### **Option A: GitHub CLI Script (Recommended for Small Teams)**

1. **Install GitHub CLI**:
   ```bash
   # macOS
   brew install gh
   
   # Windows
   winget install --id GitHub.cli
   
   # Linux
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   ```

2. **Authenticate with GitHub**:
   ```bash
   gh auth login
   ```

3. **Create your production environment file**:
   ```bash
   cp env.example .env.production
   # Edit .env.production with your actual values
   ```

4. **Run the automated setup script**:
   ```bash
   ./scripts/setup-secrets.sh .env.production
   ```

   This script will:
   - ✅ Read your `.env.production` file
   - ✅ Skip placeholder values automatically
   - ✅ Upload all real secrets to GitHub
   - ✅ Provide a summary of what was uploaded

#### **Option B: Terraform Infrastructure as Code (Recommended for Teams)**

1. **Install Terraform**:
   ```bash
   # macOS
   brew install terraform
   
   # Windows
   winget install HashiCorp.Terraform
   ```

2. **Create a `terraform/secrets.tfvars` file**:
   ```hcl
   github_token = "ghp_your_github_token"
   github_owner = "your-username"
   github_repo  = "demo-fastapi"
   
   # Database Configuration
   pghost     = "your-postgres-host"
   pgdatabase = "your-database-name"
   pguser     = "your-db-username"
   pgpassword = "your-secure-password"
   
   # API Keys
   openai_api_key    = "sk-your-actual-openai-key"
   datadog_api_key   = "your-actual-datadog-key"
   # ... etc
   ```

3. **Apply the Terraform configuration**:
   ```bash
   cd terraform
   terraform init
   terraform apply -var-file="secrets.tfvars"
   ```

#### **Option C: External Secret Management (Enterprise)**

For larger organizations, integrate with enterprise secret management:

- **HashiCorp Vault**: See `.github/workflows/deploy-with-vault.yaml`
- **AWS Secrets Manager**: Centralized secret storage in AWS
- **Azure Key Vault**: Microsoft's secret management service
- **Google Secret Manager**: Google Cloud's secret storage

### **Step 2: Local Development Setup**

1. **Copy the example file**:
   ```bash
   cp env.example .env.local
   ```

2. **Fill in your local values** in `.env.local`

3. **Load environment** (if using python-dotenv):
   ```python
   from dotenv import load_dotenv
   load_dotenv('.env.local')
   ```

### **Step 3: Production Deployment**

The GitHub Actions workflow automatically:
1. ✅ Builds the Docker image
2. ✅ Pushes to Docker Hub
3. ✅ Deploys to Synology with all secrets as environment variables
4. ✅ Verifies deployment health

## 🔒 Security Best Practices

### **What's Safe to Commit**
- ✅ `env.example` - Template with placeholder values
- ✅ `docker-compose.yml` - Uses environment variable substitution
- ✅ `DEPLOYMENT.md` - This documentation

### **What's NEVER Committed**
- ❌ `.env` - Real environment variables
- ❌ `.env.local` - Local development secrets
- ❌ `.env.production` - Production secrets
- ❌ Any file with actual API keys or passwords

### **GitHub Secrets Management**
- 🔐 **Encrypted at rest**: GitHub encrypts all secrets
- 🔐 **Encrypted in transit**: Secrets are securely transmitted
- 🔐 **Access control**: Only authorized workflows can access secrets
- 🔐 **Audit logging**: All secret access is logged

## 🚀 Deployment Workflow

### **Automatic Deployment**
1. Push to `main` branch
2. GitHub Actions builds Docker image
3. Image pushed to Docker Hub
4. SSH to Synology NAS
5. Pull latest image
6. Stop/remove old container
7. Start new container with all environment variables
8. Health check verification

### **Manual Deployment**
For manual deployments, use the docker-compose approach:

```bash
# On your Synology NAS
docker-compose up -d
```

## 🏢 Enterprise Alternatives

For larger organizations, consider these additional tools:

### **Secret Management Services**
- **HashiCorp Vault**: Enterprise secret management
- **AWS Secrets Manager**: Cloud-native secret storage
- **Azure Key Vault**: Microsoft's secret management
- **Google Secret Manager**: Google Cloud secret storage

### **Configuration Management**
- **Kubernetes ConfigMaps/Secrets**: For K8s deployments
- **Docker Swarm Secrets**: For Docker Swarm clusters
- **Ansible Vault**: For infrastructure automation

### **CI/CD Platforms**
- **GitLab CI/CD**: Built-in secret management
- **Jenkins**: With credential plugins
- **Azure DevOps**: Azure Key Vault integration
- **CircleCI**: Environment variable management

## 🔍 Verification

### **Check Environment Variables in Container**
```bash
# SSH to your Synology
docker exec images-api env | grep -E "(DD_|PG|OPENAI|DATADOG)"
```

### **Health Check**
```bash
curl http://your-synology-ip:9000/health
```

### **Container Logs**
```bash
docker logs images-api
```

## 🛠️ Troubleshooting

### **Missing Environment Variables**
- Check GitHub Secrets are properly named
- Verify workflow syntax for secret references
- Check container logs for missing variable errors

### **Database Connection Issues**
- Verify `PGHOST` points to accessible database
- Check network connectivity from container
- Validate database credentials

### **API Key Issues**
- Verify API keys are valid and not expired
- Check rate limits and quotas
- Validate key permissions and scopes

## 📚 Additional Resources

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Docker Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [12-Factor App Methodology](https://12factor.net/config)
- [OWASP Secrets Management](https://owasp.org/www-community/vulnerabilities/Insecure_Storage_of_Sensitive_Information) 