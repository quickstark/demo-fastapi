# Deployment Workflow Consolidation Summary

## Problem
You had **two** very similar self-hosted deployment workflows:
1. `deploy-self-hosted.yaml` (300 lines) - Complete but required installing dependencies
2. `deploy-self-hosted-alternative.yaml` (61 lines) - Incomplete, used Docker for SonarQube

This was confusing and redundant.

## Solution
✅ **Consolidated into ONE deployment workflow**

## Changes Made

### 1. Removed Redundant Workflow
**Deleted:** `.github/workflows/deploy-self-hosted-alternative.yaml`
- This was incomplete and no longer needed

### 2. Updated Main Workflow
**File:** `.github/workflows/deploy-self-hosted.yaml`

**Improvements:**
- ✅ **Docker-based SonarQube** - No longer requires installing unzip on host
- ✅ **Added SQL Server toggle** - `SQLSERVER_ENABLED` environment variable
- ✅ **Cleaner implementation** - Removed dependency installation step
- ✅ **Better error messages** - Clear indication when SonarQube skipped

### 3. SonarQube Implementation

**Before:**
```yaml
# Required host dependencies
- name: Install SonarQube Dependencies
  run: sudo apt-get install -y unzip

- name: SonarQube Scan
  uses: SonarSource/sonarqube-scan-action@v6  # GitHub Action
```

**After:**
```yaml
# Uses Docker - no host dependencies
- name: SonarQube Scan
  run: |
    docker run --rm \
      -e SONAR_HOST_URL="${{ secrets.SONAR_HOST_URL }}" \
      -e SONAR_TOKEN="${{ secrets.SONAR_TOKEN }}" \
      -v "$(pwd):/usr/src" \
      sonarsource/sonar-scanner-cli \
      -Dsonar.projectKey=... \
      -Dsonar.sources=main.py,src \
      -Dsonar.tests=tests
```

**Benefits:**
- No dependencies to install on host
- Consistent environment across runs
- Easier to maintain and update
- Works even if unzip isn't available

### 4. SQL Server Toggle Integration

**Added to deployment:**
```yaml
-e SQLSERVER_ENABLED="${{ secrets.SQLSERVER_ENABLED || 'true' }}" \
-e SQLSERVERHOST="${{ secrets.SQLSERVERHOST }}" \
-e SQLSERVERPORT="${{ secrets.SQLSERVERPORT }}" \
-e SQLSERVERUSER="${{ secrets.SQLSERVERUSER }}" \
-e SQLSERVERPW="${{ secrets.SQLSERVERPW }}" \
-e SQLSERVERDB="${{ secrets.SQLSERVERDB }}" \
```

**Default:** SQL Server is enabled (`true`)
**To disable:** Set GitHub Secret `SQLSERVER_ENABLED=false`

## Your Deployment Workflows Now

### 1. Self-Hosted Deployment (Primary)
- **File:** `.github/workflows/deploy-self-hosted.yaml`
- **Trigger:** Push to main or manual
- **Runner:** Your GMKTec self-hosted runner
- **Port:** 9000

### 2. GitHub-Hosted Deployment (Backup)
- **File:** `.github/workflows/deploy.yaml`
- **Trigger:** Manual only
- **Runner:** GitHub's hosted runners
- **Uses:** Tailscale for remote access

### 3. Security Scanning
- **File:** `.github/workflows/datadog-security.yml`
- **Trigger:** Push to any branch
- **Purpose:** Security analysis only (no deployment)

## How to Use

### Normal Deployment
```bash
# Just push to main
git push origin main

# Workflow automatically:
# 1. Runs SonarQube in Docker
# 2. Runs tests
# 3. Builds Docker image
# 4. Deploys to port 9000
```

### Toggle SQL Server
```bash
# In GitHub Settings → Secrets → Actions
# Add or update:
SQLSERVER_ENABLED=false  # Disable SQL Server
# or
SQLSERVER_ENABLED=true   # Enable SQL Server (default)
```

### Manual Deployment
```bash
# Go to GitHub → Actions
# Select "Build and Deploy (Self-Hosted Runner)"
# Click "Run workflow"
# Options:
#   ☐ Skip tests
#   ☐ Skip deployment (build only)
```

## Documentation Created

**New file:** `docs/DEPLOYMENT_WORKFLOWS.md`
- Complete guide to all workflows
- Required GitHub Secrets
- Troubleshooting guide
- Best practices
- SQL Server toggle instructions

## Benefits

### Before (2 Workflows)
❌ Confusing - which one to use?
❌ Redundant - duplicate code
❌ Incomplete - alternative was missing steps
❌ Dependencies - required installing packages on host

### After (1 Workflow)
✅ **Clear** - One workflow for self-hosted deployment
✅ **Complete** - All steps included
✅ **Clean** - Uses Docker, no host dependencies
✅ **Flexible** - SQL Server toggle support
✅ **Maintainable** - Single source of truth

## Testing the Changes

### Verify SonarQube Works
```bash
# Push a change to main
git commit -m "test: verify sonarqube"
git push origin main

# Check Actions tab - SonarQube should run in Docker
```

### Verify SQL Server Toggle
```bash
# Check current deployment
curl http://localhost:9000/api/v1/database-status

# Should show SQL Server status based on SQLSERVER_ENABLED secret
```

## Next Steps

1. ✅ **Consolidated workflows** - DONE
2. ✅ **Added SQL Server toggle** - DONE  
3. ✅ **Created documentation** - DONE
4. 📝 **Update GitHub Secrets** (if needed):
   - Add `SQLSERVER_ENABLED=true` (or `false`) to GitHub Secrets
   - Verify SonarQube credentials are set

## Summary

**Before:** 2 similar workflows causing confusion
**After:** 1 clean workflow with Docker-based SonarQube and SQL Server toggle

You now have a single, clear deployment workflow that:
- Uses Docker for everything (cleaner)
- Supports SQL Server toggle
- Has comprehensive documentation
- Is easier to maintain and understand

🎉 **Deployment workflows rationalized and improved!**
