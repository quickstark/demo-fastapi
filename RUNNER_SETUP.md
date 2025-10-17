# GitHub Self-Hosted Runner Setup Guide (GMKTec Local Deployment)

This guide helps you set up and manage a self-hosted GitHub Actions runner on your GMKTec Linux box for local deployment of the demo-fastapi project.

## 📋 Prerequisites

- GMKTec Linux box (Ubuntu 18.04 or later)
- Docker installed and running
- Docker Compose installed
- GitHub Personal Access Token with `repo` scope
- Application containers on the same machine (PostgreSQL, MongoDB, etc.)

## 🚀 Quick Start

### 1. Initial Setup

```bash
# Run the interactive setup script
./scripts/setup-runner.sh

# Or run specific commands
./scripts/setup-runner.sh check   # Check requirements
./scripts/setup-runner.sh setup   # Setup environment
./scripts/setup-runner.sh start   # Start the runner
```

### 2. Configure Environment

Edit `.env.runner` (created from `runner.env.example`):

```bash
# REQUIRED: Your GitHub Personal Access Token
GITHUB_ACCESS_TOKEN=github_pat_YOUR_TOKEN_HERE

# Docker group ID (automatically detected)
DOCKER_GROUP_ID=999

# Optional: Tailscale for network access
# TAILSCALE_AUTHKEY=tskey-auth-YOUR_KEY_HERE
```

### 3. Start the Runner

```bash
# Using the setup script
./scripts/setup-runner.sh start

# Or using docker-compose directly
docker-compose -f docker-compose.runner.yml --env-file .env.runner up -d
```

## 🏗️ Architecture

### Local Deployment Setup
Since the runner and application are on the same GMKTec Linux box:
- **No SSH needed** - Direct Docker commands
- **No Tailscale needed** - Everything is local
- **Simplified deployment** - No network complexity

### Runner Container
- **Image**: `ghcr.io/kevmo314/docker-gha-runner:main`
- **Features**:
  - Docker-in-Docker support via socket mount
  - Persistent cache volumes
  - Automatic registration with GitHub
  - Health checks
  - Direct access to local Docker daemon

### Key Volumes
- `/var/run/docker.sock` - Docker daemon access (required for building and deploying)
- `runner-cache` - Build cache persistence
- `runner-tools` - Tool cache persistence

### Port Configuration
- **Application**: Port 9000 (maps to container port 8080)
- **Databases**: Use standard ports or Docker network names
- **Monitoring**: Datadog agent on standard ports

## 📁 Workflow Configurations

### Self-Hosted Runner Workflow
**File**: `.github/workflows/deploy-self-hosted.yaml`
- **Triggers**: Push to main branch, manual dispatch
- **Runner**: Uses `self-hosted` label
- **Features**:
  - Docker build and push to Docker Hub
  - Local Docker deployment (same machine)
  - Automatic tests in container
  - No SSH or remote access needed
  - Port 9000 for production deployment

### GitHub-Hosted Workflow (Backup)
**File**: `.github/workflows/deploy.yaml`
- **Triggers**: Manual dispatch only (disabled automatic triggers)
- **Runner**: Uses GitHub's `ubuntu-latest`
- **Use Case**: Fallback when self-hosted runner is unavailable

## 🔧 Management Commands

### Check Status
```bash
./scripts/setup-runner.sh status
```

### View Logs
```bash
./scripts/setup-runner.sh logs
```

### Test Docker Access
```bash
./scripts/setup-runner.sh test
```

### Restart Runner
```bash
./scripts/setup-runner.sh restart
```

### Update Runner Image
```bash
./scripts/setup-runner.sh update
```

## 🔍 Troubleshooting

### Runner Not Appearing in GitHub

1. Check the token is valid:
   ```bash
   grep GITHUB_ACCESS_TOKEN .env.runner
   ```

2. Verify runner logs:
   ```bash
   docker-compose -f docker-compose.runner.yml logs runner
   ```

3. Check GitHub Settings:
   - Go to: Settings → Actions → Runners
   - Should see your runner listed

### Docker Access Issues

1. Verify socket mount:
   ```bash
   docker-compose -f docker-compose.runner.yml exec runner ls -la /var/run/docker.sock
   ```

2. Test Docker access:
   ```bash
   ./scripts/setup-runner.sh test
   ```

3. Check group permissions:
   ```bash
   docker-compose -f docker-compose.runner.yml exec runner id
   ```

### Build Failures

1. Check available disk space:
   ```bash
   df -h
   ```

2. Clean Docker resources:
   ```bash
   docker system prune -a
   ```

3. Check runner resources:
   ```bash
   docker stats github-runner
   ```

### Container Connectivity Issues

1. Check Docker network:
   ```bash
   docker network ls
   docker network inspect bridge
   ```

2. Verify container communication:
   ```bash
   docker exec github-runner ping -c 1 host.docker.internal
   ```

## 🔒 Security Considerations

### Token Security
- **Never commit** the GitHub token to version control
- Store token in `.env.runner` (gitignored)
- Use repository-scoped tokens when possible
- Rotate tokens regularly

### Container Security
- Runner has Docker socket access (privileged)
- Only use for trusted repositories
- Consider using ephemeral runners for additional security:
  ```yaml
  environment:
    EPHEMERAL: "true"
  ```

### Network Security
- All operations are local (no external network access needed for deployment)
- Use GitHub Secrets for sensitive data
- Container-to-container communication via Docker networks

## 📝 Configuration Options

### Runner Labels
Customize labels in `docker-compose.runner.yml`:
```yaml
LABELS: self-hosted,linux,x64,ubuntu,docker,gpu  # Add custom labels
```

### Resource Limits
Uncomment in `docker-compose.runner.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
```

### Multiple Runners
Scale up runners:
```yaml
deploy:
  replicas: 3  # Run 3 parallel runners
```

## 🎯 Deployment Strategy

### Automatic Local Deployment
The workflow automatically:
1. Builds the Docker image
2. Pushes to Docker Hub
3. Deploys locally on the same GMKTec machine
4. Runs on port 9000

### Manual Options
When triggering manually, you can:
- **Skip tests**: Speed up deployment
- **Skip deployment**: Build and push only, no local deployment

## 📊 Monitoring

### Runner Metrics
```bash
# CPU and memory usage
docker stats github-runner

# Disk usage
docker system df
```

### GitHub Actions Dashboard
- View runs: https://github.com/quickstark/demo-fastapi/actions
- Runner status: Settings → Actions → Runners

### Datadog Integration
Deployments are automatically tracked in Datadog APM when configured.

## 🆘 Support

For issues or questions:
1. Check runner logs: `./scripts/setup-runner.sh logs`
2. Review GitHub Actions documentation
3. Check the troubleshooting section above
4. Open an issue in the repository

## 📚 Additional Resources

- [GitHub Self-Hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Docker-in-Docker Best Practices](https://jpetazzo.github.io/2015/09/03/do-not-use-docker-in-docker-for-ci/)
- [GitHub Actions Security](https://docs.github.com/en/actions/security-guides)
