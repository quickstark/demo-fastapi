# Datadog Deployment Tracking

This document explains how Datadog deployment tracking is integrated into our GitHub Actions CI/CD pipeline.

## Overview

Our GitHub Actions workflow automatically notifies Datadog whenever a successful deployment occurs, enabling:

- **Deployment Visibility**: Track deployment frequency, success rates, and timing
- **Correlation with Metrics**: See how deployments affect application performance
- **Incident Response**: Quickly identify if issues correlate with recent deployments
- **Release Management**: Monitor deployment patterns across environments

## How It Works

### 1. Datadog CI Installation

The workflow installs the `@datadog/datadog-ci` CLI tool:

```yaml
- name: Install Datadog CI
  run: |
    npm install -g @datadog/datadog-ci
    datadog-ci version
```

### 2. Deployment Marking

After a successful deployment to Synology, the workflow marks the deployment in Datadog:

```yaml
- name: Mark Deployment in Datadog
  if: steps.synology_deploy.outcome == 'success'
  env:
    DD_API_KEY: ${{ secrets.DATADOG_API_KEY }}
    DD_SITE: datadoghq.com
    DD_BETA_COMMANDS_ENABLED: 1
    DD_GITHUB_JOB_NAME: build-and-deploy
  run: |
    datadog-ci deployment mark \
      --env "${{ secrets.DD_ENV }}" \
      --service "${{ secrets.DD_SERVICE }}" \
      --revision "$SHORT_SHA" \
      --tags "deployment_method:github_actions" \
      --tags "repository:${{ github.repository }}" \
      --tags "branch:${{ github.ref_name }}" \
      --tags "actor:${{ github.actor }}" \
      --tags "workflow:${{ github.workflow }}" \
      --tags "run_id:${{ github.run_id }}" \
      --tags "deploy_time:$DEPLOY_TIME" \
      --no-fail
```

## Required Environment Variables

The following secrets must be configured in GitHub:

| Secret | Description | Example |
|--------|-------------|---------|
| `DATADOG_API_KEY` | Your Datadog API key | `abc123...` |
| `DD_SERVICE` | Service name in Datadog | `images-api` |
| `DD_ENV` | Environment name | `production` |

## Deployment Data Captured

Each deployment event includes:

### Core Information
- **Service**: The name of the service being deployed (`DD_SERVICE`)
- **Environment**: Target environment (`DD_ENV`)
- **Revision**: Git commit SHA (first 7 characters)
- **Timestamp**: UTC timestamp of deployment

### GitHub Context Tags
- `deployment_method:github_actions`
- `repository:quickstark/demo-fastapi`
- `branch:main`
- `actor:username` (who triggered the deployment)
- `workflow:Build and Deploy`
- `run_id:123456789` (GitHub Actions run ID)
- `deploy_time:2024-01-15T10:30:00Z`

## Viewing Deployments in Datadog

### 1. Deployments Page
Navigate to **APM > Deployments** in Datadog to see:
- Deployment timeline
- Success/failure rates
- Deployment frequency
- Service-specific deployment history

### 2. Service Overview
In **APM > Services**, select your service to see:
- Deployment markers on performance graphs
- Correlation between deployments and metrics
- Error rate changes after deployments

### 3. Dashboards
Deployment events can be overlaid on any dashboard using:
- Event overlay widgets
- Deployment markers on timeseries graphs
- Custom queries filtering by deployment tags

## Troubleshooting

### Common Issues

1. **Missing API Key**
   ```
   Error: DD_API_KEY is required
   ```
   **Solution**: Ensure `DATADOG_API_KEY` secret is set in GitHub

2. **Beta Commands Not Enabled**
   ```
   Error: Beta commands are not enabled
   ```
   **Solution**: The workflow sets `DD_BETA_COMMANDS_ENABLED=1` automatically

3. **Deployment Not Showing**
   - Check GitHub Actions logs for the "Mark Deployment in Datadog" step
   - Verify the deployment step completed successfully
   - Ensure the correct Datadog site is configured (`DD_SITE=datadoghq.com`)

### Debug Information

The workflow logs include:
```
Marking deployment in Datadog...
Service: images-api
Environment: production
Revision: abc1234
Deploy Time: 2024-01-15T10:30:00Z
✅ Deployment marked in Datadog successfully!
```

## Advanced Configuration

### Custom Tags
Add additional tags to deployments by modifying the `--tags` parameters:

```yaml
--tags "team:backend" \
--tags "release_type:hotfix" \
--tags "deployment_tool:custom"
```

### Rollback Detection
For rollback deployments, add the `--is-rollback` flag:

```yaml
datadog-ci deployment mark \
  --env "${{ secrets.DD_ENV }}" \
  --service "${{ secrets.DD_SERVICE }}" \
  --is-rollback
```

### Multiple Services
If deploying multiple services, create separate deployment marks:

```yaml
# Mark deployment for each service
datadog-ci deployment mark --env prod --service api-service --revision $SHA
datadog-ci deployment mark --env prod --service worker-service --revision $SHA
```

## Integration with Monitoring

### Alerts and Notifications
- Set up monitors to alert on deployment failures
- Create notifications for successful deployments
- Monitor error rates after deployments

### SLOs and SLIs
- Track deployment frequency as an SLI
- Monitor deployment success rate
- Measure time to recovery after failed deployments

### Incident Response
- Use deployment timeline during incident investigation
- Correlate issues with recent deployments
- Quick rollback identification

## References

- [Datadog CI Documentation](https://docs.datadoghq.com/continuous_delivery/deployments/ciproviders/)
- [GitHub Actions Integration](https://docs.datadoghq.com/continuous_delivery/deployments/ciproviders/#github-actions)
- [Deployment Visibility](https://docs.datadoghq.com/continuous_delivery/deployments/) 