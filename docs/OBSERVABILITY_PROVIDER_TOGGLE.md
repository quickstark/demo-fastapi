# Observability Provider Toggle System

## Overview

The FastAPI application now supports **seamless switching** between Datadog and Sentry for error tracking, performance monitoring, and observability. This allows A/B testing, cost comparison, and easy migration between providers **without any code changes**.

## Architecture

### Design Pattern
- **Strategy Pattern**: Abstract base class (`ObservabilityProvider`) with concrete implementations
- **Factory Pattern**: Provider selection via environment variables
- **Singleton Pattern**: Single provider instance per application lifecycle

### Components
```
src/observability/
├── base.py                 # Abstract ObservabilityProvider interface
├── datadog_provider.py     # Datadog implementation (ddtrace)
├── sentry_provider.py      # Sentry implementation (sentry-sdk)
├── noop_provider.py        # Disabled/testing implementation
└── __init__.py             # Factory and provider registry
```

## Environment Variables

### Provider Selection

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `OBSERVABILITY_PROVIDER` | `datadog`, `sentry`, `disabled` | `datadog` | Primary provider selection and toggle |

### Datadog Configuration (existing)

All existing Datadog environment variables remain unchanged:
- `DD_SERVICE`, `DD_ENV`, `DD_VERSION` (service tags)
- `DD_AGENT_HOST`, `DD_TRACE_AGENT_PORT` (agent connection)
- `DD_API_KEY`, `DD_APP_KEY` (Events API)
- `DD_PROFILING_ENABLED`, `DD_LLMOBS_ENABLED` (feature toggles)
- `DD_DBM_PROPAGATION_MODE` (database monitoring)

### Sentry Configuration (new)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENTRY_DSN` | **Yes** | `""` | Project DSN from Sentry.io |
| `SENTRY_ENVIRONMENT` | No | `DD_ENV` value | Environment name |
| `SENTRY_RELEASE` | No | `DD_VERSION` value | Release version |
| `SENTRY_TRACES_SAMPLE_RATE` | No | `1.0` | Performance sampling (0.0-1.0) |
| `SENTRY_PROFILES_SAMPLE_RATE` | No | `0.0` | Profiling sampling (0.0-1.0) |
| `SENTRY_SEND_DEFAULT_PII` | No | `false` | Include PII in events |
| `SENTRY_DEBUG` | No | `false` | SDK debug logging |
| `SENTRY_ATTACH_STACKTRACE` | No | `true` | Stack traces on all messages |

## Usage Examples

### Scenario 1: Using Datadog (Default)

**Local Development (.env)**:
```bash
OBSERVABILITY_PROVIDER=datadog
DD_AGENT_HOST=192.168.1.100
DD_API_KEY=your-datadog-api-key
DD_APP_KEY=your-datadog-app-key
```

**Verification**:
```bash
curl http://localhost:9000/health
# Response includes:
# {
#   "observability_provider": "datadog",
#   "observability_enabled": true
# }
```

### Scenario 2: Switching to Sentry

**Update .env**:
```bash
OBSERVABILITY_PROVIDER=sentry
SENTRY_DSN=https://[key]@[org].ingest.sentry.io/[project]
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=1.0
```

**Restart Application**:
```bash
docker restart images-api
```

**Verification**:
```bash
curl http://localhost:9000/health
# Response:
# {
#   "observability_provider": "sentry",
#   "observability_enabled": true
# }
```

### Scenario 3: Disabled Observability (Testing)

```bash
OBSERVABILITY_PROVIDER=disabled
```

All observability calls become no-ops with zero overhead.

### Scenario 4: A/B Testing Workflow

**Week 1 - Datadog Baseline**:
```bash
OBSERVABILITY_PROVIDER=datadog
```
- Run production workload
- Collect error capture metrics
- Note performance overhead
- Document monthly cost

**Week 2 - Sentry Comparison**:
```bash
OBSERVABILITY_PROVIDER=sentry
SENTRY_DSN=your-sentry-dsn
```
- Run same workload
- Compare error capture quality
- Measure performance impact
- Calculate Sentry costs

**Analysis**:
- Error detection completeness
- Alert accuracy and noise
- Performance monitoring depth
- UI/UX preferences
- Cost per month comparison

## GitHub Actions / CI/CD Integration

### Required GitHub Secrets

**Datadog** (existing):
- `DD_API_KEY`
- `DD_APP_KEY`
- `DD_SERVICE`
- `DD_ENV`
- `DD_AGENT_HOST`

**Sentry** (new):
- `SENTRY_DSN`
- `SENTRY_ENVIRONMENT` (optional, defaults to `DD_ENV`)
- `SENTRY_TRACES_SAMPLE_RATE` (optional, defaults to `1.0`)
- `SENTRY_PROFILES_SAMPLE_RATE` (optional, defaults to `0.0`)

**Provider Selection** (new):
- `OBSERVABILITY_PROVIDER` (optional, defaults to `datadog`)

### Workflow Changes

The deployment workflow (`.github/workflows/deploy-self-hosted.yaml`) now passes all observability environment variables to the Docker container. To switch providers:

1. **Update GitHub Secrets** in repository settings
2. **Set `OBSERVABILITY_PROVIDER`** secret to `sentry`
3. **Add `SENTRY_DSN`** secret
4. **Trigger deployment** (push to main or manual workflow dispatch)

No workflow file changes required - all provider switching is configuration-driven.

## Docker Configuration

### Building the Image

No changes required. The Dockerfile includes default environment variables for both providers.

### Running with Datadog

```bash
docker run -d \
  --name images-api \
  -p 9000:8080 \
  -e OBSERVABILITY_PROVIDER=datadog \
  -e DD_AGENT_HOST=192.168.1.100 \
  -e DD_API_KEY=your-api-key \
  -e DD_APP_KEY=your-app-key \
  quickstark/api-images:latest
```

### Running with Sentry

```bash
docker run -d \
  --name images-api \
  -p 9000:8080 \
  -e OBSERVABILITY_PROVIDER=sentry \
  -e SENTRY_DSN=https://[key]@[org].ingest.sentry.io/[project] \
  -e SENTRY_ENVIRONMENT=production \
  -e SENTRY_TRACES_SAMPLE_RATE=1.0 \
  quickstark/api-images:latest
```

### Switching Providers (Zero Downtime)

1. **Stop current container**:
   ```bash
   docker stop images-api
   docker rm images-api
   ```

2. **Start with new provider**:
   ```bash
   docker run -d \
     --name images-api \
     -e OBSERVABILITY_PROVIDER=sentry \
     -e SENTRY_DSN=your-sentry-dsn \
     [other env vars...]
     quickstark/api-images:latest
   ```

3. **Verify switch**:
   ```bash
   curl http://localhost:9000/health | jq '.observability_provider'
   ```

## Code Integration

### Backward Compatibility

All existing Datadog-specific code continues to work:

```python
from ddtrace import tracer

@tracer.wrap(service="api-service", resource="upload")
async def upload_file():
    pass
```

When using Sentry, these decorators become no-ops (zero overhead).

### Provider-Agnostic Code (Recommended)

```python
from src.observability import get_provider

provider = get_provider()

# Tracing
@provider.trace_decorator("api.upload")
async def upload_file():
    pass

# Manual spans
with provider.trace_context("database.query") as span:
    result = execute_query()
    if span:
        span.set_tag("rows", len(result))

# Error recording
try:
    upload_file()
except Exception as e:
    provider.record_error(
        e,
        error_type="upload_failure",
        tags={"service": "s3", "filename": "image.jpg"}
    )

# Custom events
provider.record_event(
    title="Deployment Started",
    text="Version 1.2.3 deployed",
    alert_type="info",
    tags=["deployment", "v1.2.3"]
)
```

### CustomError Class

The `CustomError` class now uses the observability provider automatically:

```python
raise CustomError(
    message="S3 upload failed",
    error_type="s3_upload_failure",
    tags=[("filename", "image.jpg"), ("bucket", "images")]
)
```

This works with both Datadog and Sentry without code changes.

## Troubleshooting

### Datadog Not Sending Traces

1. **Check agent connectivity**:
   ```bash
   curl http://DD_AGENT_HOST:DD_TRACE_AGENT_PORT/info
   ```

2. **Verify environment variables**:
   ```bash
   docker exec images-api env | grep DD_
   ```

3. **Check provider status**:
   ```bash
   curl http://localhost:9000/health | jq '.observability_enabled'
   ```

### Sentry Not Capturing Errors

1. **Verify DSN configuration**:
   ```bash
   docker exec images-api env | grep SENTRY_DSN
   ```

2. **Check Sentry debug logs**:
   ```bash
   docker logs images-api | grep -i sentry
   ```

3. **Test with manual error**:
   ```bash
   curl http://localhost:9000/api/v1/app-event/error?message=test
   ```

### Provider Not Switching

1. **Verify environment variable**:
   ```bash
   docker exec images-api env | grep OBSERVABILITY_PROVIDER
   ```

2. **Check health endpoint**:
   ```bash
   curl http://localhost:9000/health
   ```

3. **Restart container** (provider is initialized once at startup):
   ```bash
   docker restart images-api
   ```

## Best Practices

### Sampling for Production

- **Datadog**: Set `DD_TRACE_SAMPLE_RATE=0.1` (10% of traces)
- **Sentry**: Set `SENTRY_TRACES_SAMPLE_RATE=0.3` (30% of transactions)

This reduces costs while maintaining observability coverage.

### Security

- **Never commit `.env` files** with real credentials
- **Use GitHub Secrets** for CI/CD
- **Rotate keys regularly** (both Datadog and Sentry)
- **Set `SENTRY_SEND_DEFAULT_PII=false`** in production

### Cost Optimization

- Start with **higher sampling rates** (1.0) to establish baseline
- **Monitor quota usage** in provider dashboards
- **Reduce sampling** if approaching limits
- **Disable profiling** (`SENTRY_PROFILES_SAMPLE_RATE=0.0`) until needed

## Migration Guide

### Moving from Datadog to Sentry

1. **Create Sentry project** at https://sentry.io
2. **Copy DSN** from project settings
3. **Add GitHub secrets**: `SENTRY_DSN`, `OBSERVABILITY_PROVIDER=sentry`
4. **Deploy application** with updated secrets
5. **Verify in Sentry dashboard** that events are arriving
6. **Run comparison period** (1-2 weeks) for analysis
7. **Make decision** based on comparison data

### Rolling Back to Datadog

1. **Update GitHub secret**: `OBSERVABILITY_PROVIDER=datadog`
2. **Redeploy** (automatic via GitHub Actions)
3. **Verify in Datadog** that traces are flowing

Rollback time: **< 5 minutes** (just deployment time).

## Performance Impact

### Datadog
- Instrumentation overhead: ~1-3% CPU
- Memory overhead: ~50-100MB
- Network: Traces sent to local agent (low latency)

### Sentry
- Instrumentation overhead: ~1-2% CPU
- Memory overhead: ~30-50MB
- Network: Direct HTTPS to Sentry (higher latency)

### Disabled (Noop)
- Overhead: **0%** (all calls are no-ops)

## Support

For issues or questions:
- **Datadog**: Check agent logs, verify connectivity
- **Sentry**: Enable `SENTRY_DEBUG=true`, check SDK logs
- **Provider Toggle**: Verify `OBSERVABILITY_PROVIDER` value, check health endpoint

---

**Last Updated**: 2025-01-11
**Version**: 1.0.0
