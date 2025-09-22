# GMKTec Host Migration Checklist

This document outlines the steps required to migrate your FastAPI container from Synology to GMKTec host.

## Prerequisites

### 1. SSH Key Setup
Generate a new SSH key pair for GitHub Actions:
```bash
# On your local machine
ssh-keygen -t ed25519 -f ~/.ssh/gmktec_github_actions -C "github-actions@gmktec"

# If ed25519 is not supported, use RSA:
ssh-keygen -t rsa -b 4096 -f ~/.ssh/gmktec_github_actions -C "github-actions@gmktec"
```

### 2. Configure GMKTec Host
On your GMKTec host (100.66.93.87):
```bash
# Add the public key to authorized_keys
cat ~/.ssh/gmktec_github_actions.pub >> ~/.ssh/authorized_keys

# Ensure correct permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# Install Docker if not already installed
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (replace 'username' with your actual username)
sudo usermod -aG docker username

# Logout and login again for group changes to take effect
```

### 3. Tailscale Setup
1. **Create an OAuth API client** (recommended):
   - Go to https://tailscale.com/s/oauth-clients
   - Create a new OAuth client for GitHub Actions
   - Grant the `auth_keys` scope (required for Tailscale GitHub Action v3)
   - Note the Client ID and Client Secret
   - These will be stored as two separate GitHub secrets:
     - `TAILSCALE_OAUTH_CLIENT_ID`
     - `TAILSCALE_OAUTH_CLIENT_SECRET`

2. **Alternative: Create an Auth Key** (less secure, not recommended):
   - Go to Tailscale admin console
   - Generate a new auth key
   - Make it reusable if you plan frequent deployments
   - Set appropriate expiration
   - Store as `TAILSCALE_AUTHKEY`

## GitHub Secrets Configuration

Add the following secrets to your GitHub repository (Settings → Secrets and variables → Actions):

### New Secrets Required:
| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `TAILSCALE_OAUTH_CLIENT_ID` | Tailscale OAuth Client ID | `k1234...` |
| `TAILSCALE_OAUTH_CLIENT_SECRET` | Tailscale OAuth Client Secret | `tskey-client-k1234...` |
| `GMKTEC_USER` | SSH username for GMKTec host | `your-username` |
| `GMKTEC_SSH_KEY` | Private SSH key content (entire file) | Contents of `~/.ssh/gmktec_github_actions` |
| `GMKTEC_SSH_PASSPHRASE` | SSH key passphrase (if set, otherwise leave empty) | `your-passphrase` or empty |

### Secrets to Remove (No Longer Needed):
- `SYNOLOGY_HOST`
- `SYNOLOGY_SSH_PORT`
- `SYNOLOGY_USER`
- `SYNOLOGY_SSH_KEY`
- `SYNOLOGY_SSH_PASSPHRASE`

### Secrets to Keep (Unchanged):
- `DD_SERVICE`
- `DD_ENV`
- `DD_VERSION`
- `DD_AGENT_HOST` (new: set to 192.168.1.200)
- `PGHOST` (update to: 192.168.1.100)
- `PGPORT` (update to: 9001)
- `PGDATABASE`
- `PGUSER`
- `PGPASSWORD`
- `SQLSERVERHOST` (update to: 192.168.1.100)
- `SQLSERVERPORT` (update to: 9002)
- `SQLSERVERUSER`
- `SQLSERVERPW`
- `SQLSERVERDB`
- `OPENAI_API_KEY`
- `DD_API_KEY`
- `DD_APP_KEY`
- `SES_REGION`
- `SES_FROM_EMAIL`
- `NOTION_API_KEY`
- `NOTION_DATABASE_ID`
- `AMAZON_KEY_ID`
- `AMAZON_KEY_SECRET`
- `AMAZON_S3_BUCKET`
- `MONGO_CONN`
- `MONGO_USER`
- `MONGO_PW`
- `BUG_REPORT_EMAIL`
- `DOCKERHUB_USER`
- `DOCKERHUB_TOKEN`

## Environment Changes Summary

### Database Connections (Update in GitHub Secrets)
| Service | Environment Variable | New Value |
|---------|---------------------|-----------|
| PostgreSQL | `PGHOST` | `192.168.1.100` |
| PostgreSQL | `PGPORT` | `9001` |
| SQL Server | `SQLSERVERHOST` | `192.168.1.100` |
| SQL Server | `SQLSERVERPORT` | `9002` |
| MongoDB | No change | No change |

### Datadog Configuration
| Setting | Environment Variable | New Value |
|---------|---------------------|-----------|
| Datadog Agent | `DD_AGENT_HOST` | `192.168.1.200` |

### Container Configuration
| Setting | Change | Notes |
|---------|--------|-------|
| Container Name | `images-api` | Unchanged |
| Port Mapping | `9000:8080` | Unchanged |
| PUID/PGID | **Removed** | Not needed on GMKTec |

## Deployment Workflow Changes

The GitHub Actions workflow has been updated with:

1. **Tailscale OAuth Integration**: Uses OAuth client (not authkey) with Tailscale GitHub Action v3
2. **Updated SSH Target**: Now connects to `100.66.93.87` (GMKTec via Tailscale)
3. **Simplified Docker Detection**: Standard Linux Docker installation expected
4. **Database Configuration**: Database hosts/ports updated via GitHub Secrets (not hardcoded)
5. **Added DD_AGENT_HOST**: Datadog Agent host configuration via GitHub Secrets

## Testing the Migration

### 1. Pre-Deployment Verification
```bash
# From your local machine, test SSH connection
ssh -i ~/.ssh/gmktec_github_actions username@100.66.93.87

# Test Docker access
docker --version
docker ps

# Test network connectivity to databases
nc -zv 192.168.1.100 9001  # PostgreSQL
nc -zv 192.168.1.100 9002  # SQL Server
nc -zv 192.168.1.200 8126  # Datadog Agent (StatsD port)
```

### 2. Manual Deployment Test
Before pushing to trigger GitHub Actions, test manually:
```bash
# Pull and run the container manually on GMKTec
docker pull quickstark/api-images:latest

docker run -d \
  --name images-api-test \
  --restart unless-stopped \
  -p 9000:8080 \
  -e DD_AGENT_HOST="192.168.1.200" \
  -e PGHOST="192.168.1.100" \
  -e PGPORT="9001" \
  -e SQLSERVERHOST="192.168.1.100" \
  -e SQLSERVERPORT="9002" \
  # ... (add other environment variables as needed)
  quickstark/api-images:latest

# Check logs
docker logs images-api-test

# Test API endpoint
curl http://localhost:9000/health

# Clean up test container
docker stop images-api-test
docker rm images-api-test
```

### 3. GitHub Actions Deployment
1. Commit and push the updated workflow file
2. Monitor the Actions tab in GitHub
3. Check deployment logs for any issues
4. Verify the application is running on GMKTec host

## Rollback Plan

If issues occur, you can quickly rollback:

1. **Revert the workflow file** to the previous version pointing to Synology
2. **Restore the old secrets** in GitHub if removed
3. **Manually deploy** the last known good image to GMKTec

## Post-Migration Checklist

- [ ] SSH keys generated and configured
- [ ] GMKTec host accessible via Tailscale
- [ ] Docker installed and user has permissions
- [ ] GitHub secrets updated
- [ ] Workflow file updated and committed
- [ ] Databases accessible from GMKTec host
- [ ] Datadog Agent accessible at 192.168.1.200
- [ ] First deployment successful
- [ ] API health check passing
- [ ] Datadog deployment marker working
- [ ] Old Synology container stopped/removed
- [ ] Old secrets removed from GitHub (cleanup)

## Troubleshooting

### Common Issues

1. **Tailscale Connection Failed**
   - Verify auth key is valid and not expired
   - Check Tailscale admin console for device authorization
   - Consider using OAuth client instead of auth key

2. **SSH Connection Failed**
   - Verify GMKTec host is accessible via Tailscale
   - Check SSH key permissions (600 for private key)
   - Ensure public key is in authorized_keys

3. **Docker Permission Denied**
   - Ensure user is in docker group: `groups username`
   - Logout and login again after adding to group
   - Or configure sudo access for docker commands

4. **Database Connection Failed**
   - Verify firewall rules allow connections
   - Check database services are running
   - Test connectivity with `telnet` or `nc`

5. **Datadog Agent Not Found**
   - Verify agent is running at 192.168.1.200
   - Check StatsD port (8125) and APM port (8126) are open
   - Review Datadog Agent logs
