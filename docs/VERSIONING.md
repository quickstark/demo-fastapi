# Semantic Versioning & Deployment Guide

## Overview

This project uses **semantic versioning** to track releases and integrate with Datadog's Continuous Deployment (CD) feature. Version information is managed through a `VERSION` file and automatically synchronized with Git tags and deployment tracking.

## Version Format

We follow [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH

Example: 1.2.3
```

- **MAJOR**: Incompatible API changes or major breaking changes
- **MINOR**: New features, backwards-compatible functionality
- **PATCH**: Bug fixes, patches, small improvements

## How It Works

### System Components

1. **`VERSION` file** (repo root)
   - Single source of truth for current version
   - Plain text file containing version number (e.g., "1.0.0")

2. **`.github/workflows/version-tag.yaml`**
   - Runs when VERSION file changes
   - Creates Git tag (e.g., v1.0.0)
   - Creates GitHub Release automatically

3. **`.github/workflows/deploy-self-hosted.yaml`**
   - Reads VERSION file during deployment
   - Sets DD_VERSION environment variable
   - Reports version to Datadog CD

4. **`main.py`**
   - Reads VERSION file at startup
   - Falls back to DD_VERSION env var if file not available
   - Exposes version via `/health` endpoint

### Workflow Diagram

```
1. Developer updates VERSION file (1.0.0 → 1.1.0)
   ↓
2. Commit and push to main branch
   ↓
3. version-tag.yaml workflow runs
   ├─ Creates Git tag: v1.1.0
   └─ Creates GitHub Release
   ↓
4. deploy-self-hosted.yaml workflow runs
   ├─ Reads VERSION file: 1.1.0
   ├─ Builds Docker image
   ├─ Sets DD_VERSION=1.1.0 in container
   ├─ Deploys to self-hosted runner
   └─ Marks deployment in Datadog with version 1.1.0
   ↓
5. Datadog CD detects new version
   └─ Tracks deployment, creates deployment event
```

## How to Bump Versions

### Step 1: Decide Version Bump Type

Determine if your changes warrant a MAJOR, MINOR, or PATCH version bump:

**PATCH** (x.x.X) - Bug fixes, small improvements:
```
1.0.0 → 1.0.1
```

**MINOR** (x.X.0) - New features, backwards-compatible:
```
1.0.1 → 1.1.0
```

**MAJOR** (X.0.0) - Breaking changes, major rewrites:
```
1.1.0 → 2.0.0
```

### Step 2: Update VERSION File

Edit the `VERSION` file in the repository root:

```bash
# Open the file
nano VERSION

# Change the content (example)
# From: 1.0.0
# To:   1.1.0

# Save and exit
```

### Step 3: Commit and Push

```bash
git add VERSION
git commit -m "Bump version to 1.1.0"
git push origin main
```

### Step 4: Automated Magic ✨

The system automatically:
- Creates Git tag `v1.1.0`
- Creates GitHub Release
- Triggers deployment with new version
- Reports to Datadog CD

## Verifying Deployments

### Check Version in Application

Visit the health endpoint:
```bash
curl http://localhost:9000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "your-service-name",
  "version": "1.1.0",
  "environment": "production"
}
```

### Check Git Tags

```bash
# List all tags
git tag -l

# Show latest tag
git describe --tags --abbrev=0
```

### Check GitHub Releases

Visit: `https://github.com/YOUR_ORG/demo-fastapi/releases`

### Check Datadog CD

1. Go to Datadog → APM → Service Catalog
2. Select your service
3. Click "Deployments" tab
4. Verify new version appears with deployment timestamp

## Datadog CD Integration

### What Gets Tracked

Datadog tracks deployments using the `DD_VERSION` environment variable:

- **Version**: Semantic version from VERSION file (e.g., "1.1.0")
- **Environment**: From DD_ENV secret (e.g., "production")
- **Service**: From DD_SERVICE secret (e.g., "fastapi-app")
- **Timestamp**: Automatic deployment time
- **Git SHA**: Added as tag for reference

### Deployment Markers

Each deployment creates a marker in Datadog with:
- Semantic version as primary identifier
- Git SHA for reference
- Deployment method (self_hosted)
- Repository and branch info
- Actor who triggered deployment

### Why Semantic Versions Matter

Datadog CD uses versions to:
- **Group related deployments** across environments
- **Track version progression** (dev → staging → prod)
- **Identify version-related issues** in APM traces
- **Create deployment events** for correlation with metrics
- **Generate deployment velocity metrics**

## Best Practices

### Version Bump Timing

**Do bump version when:**
- ✅ Merging a feature branch to main
- ✅ Releasing a bug fix
- ✅ Making configuration changes that affect behavior
- ✅ Updating dependencies with breaking changes

**Don't bump version for:**
- ❌ Documentation updates only
- ❌ CI/CD configuration changes that don't affect the app
- ❌ Code comments or formatting changes
- ❌ Development branch commits (bump when merging to main)

### Version Control Tips

1. **One version bump per release**: Don't bump multiple times before deploying
2. **Meaningful commit messages**: Include version bump reason
3. **Tag protection**: Consider protecting tags in GitHub settings
4. **Release notes**: Use GitHub Releases to document changes

### Example Workflow

```bash
# Feature development (on feature branch)
git checkout -b feature/new-api
# ... make changes ...
git commit -m "Add new API endpoint"

# When ready to release (merge to main)
git checkout main
git merge feature/new-api

# Bump version appropriately
echo "1.1.0" > VERSION
git add VERSION
git commit -m "Bump version to 1.1.0 - Add new API endpoint"
git push origin main

# Automation handles the rest! 🎉
```

## Troubleshooting

### Version Not Updating in Datadog

**Symptom**: Datadog still shows old version after deployment

**Solution**:
1. Check workflow logs: Did deploy-self-hosted.yaml run successfully?
2. Verify VERSION file was read: Look for "📦 Deployment Version: X.X.X" in logs
3. Check container environment: `docker exec images-api printenv DD_VERSION`
4. Verify datadog-ci ran: Look for "✅ Deployment marked in Datadog" in logs

### Git Tag Already Exists

**Symptom**: version-tag.yaml fails with "tag already exists"

**Solution**:
1. Check if you forgot to bump VERSION file
2. Delete old tag if needed: `git tag -d v1.0.0 && git push origin :refs/tags/v1.0.0`
3. Update VERSION to new unique version

### Application Shows Wrong Version

**Symptom**: `/health` endpoint returns incorrect version

**Solution**:
1. Check if VERSION file is in Docker image: `docker exec images-api cat /app/VERSION`
2. Verify DD_VERSION env var: `docker exec images-api printenv DD_VERSION`
3. Check application logs for version loading messages
4. Restart container to pick up new VERSION file

### Datadog CI Not Available

**Symptom**: "Datadog CI not available, skipping deployment marking"

**Solution**:
1. Install datadog-ci on self-hosted runner: `npm install -g @datadog/datadog-ci`
2. Or ensure npm is available for local installation
3. Verify DD_API_KEY is set in GitHub secrets
4. Check workflow logs for installation errors

## Migration Notes

### Updating from Commit SHA to Semantic Versioning

If you previously used commit SHAs as versions:

1. Old deployments in Datadog will still show SHA versions
2. New deployments will use semantic versions
3. There's no need to clean up old data
4. Datadog will start tracking new semantic versions going forward

### Updating Existing Deployments

To retroactively mark an existing deployment:

```bash
# Manually mark deployment with datadog-ci
datadog-ci deployment mark \
  --env production \
  --service your-service \
  --revision 1.0.0 \
  --tags "deployment_method:manual"
```

## Additional Resources

- [Semantic Versioning Specification](https://semver.org/)
- [Datadog Deployment Tracking Documentation](https://docs.datadoghq.com/tracing/deployment_tracking/)
- [GitHub Actions Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

---

**Questions or Issues?**

If you encounter problems with versioning or deployment tracking, check:
1. GitHub Actions workflow logs
2. Docker container logs: `docker logs images-api`
3. Datadog deployment markers: APM → Service → Deployments tab
4. This documentation's troubleshooting section
