# Observability Provider Quick Start

## 🎯 TL;DR - Switching Providers

### Use Datadog (Default)
```bash
OBSERVABILITY_PROVIDER=datadog
DD_AGENT_HOST=192.168.1.100
DD_API_KEY=your-key
```

### Use Sentry
```bash
OBSERVABILITY_PROVIDER=sentry
SENTRY_DSN=https://[key]@[org].ingest.sentry.io/[project]
```

### Disable All Observability
```bash
OBSERVABILITY_PROVIDER=disabled
```

**That's it!** Restart your container and the provider switches automatically.

---

## ⚡ Quick Commands

### Check Current Provider
```bash
curl http://localhost:9000/health | jq '.observability_provider'
```

### Switch to Sentry (Local Docker)
```bash
docker stop images-api
docker run -d --name images-api \
  -p 9000:8080 \
  -e OBSERVABILITY_PROVIDER=sentry \
  -e SENTRY_DSN=your-sentry-dsn \
  quickstark/api-images:latest
```

### Switch to Datadog (Local Docker)
```bash
docker stop images-api
docker run -d --name images-api \
  -p 9000:8080 \
  -e OBSERVABILITY_PROVIDER=datadog \
  -e DD_AGENT_HOST=192.168.1.100 \
  quickstark/api-images:latest
```

---

## 📋 GitHub Actions Deployment

### Required Secrets for Datadog
- `OBSERVABILITY_PROVIDER` = `datadog`
- `DD_API_KEY`
- `DD_APP_KEY`
- `DD_AGENT_HOST`

### Required Secrets for Sentry
- `OBSERVABILITY_PROVIDER` = `sentry`
- `SENTRY_DSN` (from Sentry project settings)

**No workflow file changes needed** - just update secrets and deploy!

---

## 🧪 A/B Testing Workflow

### Week 1: Datadog
```bash
# Set GitHub secret: OBSERVABILITY_PROVIDER=datadog
# Deploy via GitHub Actions
# Collect metrics: error count, performance overhead, cost
```

### Week 2: Sentry
```bash
# Update GitHub secret: OBSERVABILITY_PROVIDER=sentry
# Add SENTRY_DSN secret
# Deploy via GitHub Actions
# Collect same metrics
```

### Compare & Decide
- Error capture quality
- Performance impact
- Monthly cost
- UI/UX preferences

---

## 🔍 Getting Sentry DSN

1. Go to https://sentry.io
2. Create a new project
3. Navigate to **Settings** → **Projects** → **[Your Project]** → **Client Keys (DSN)**
4. Copy the DSN (format: `https://[key]@[org].ingest.sentry.io/[project]`)
5. Add to `.env` or GitHub Secrets

---

## ⚙️ Environment Variables Reference

### Provider Selection
| Variable | Values | Default |
|----------|--------|---------|
| `OBSERVABILITY_PROVIDER` | `datadog`, `sentry`, `disabled` | `datadog` |

### Sentry Essentials
| Variable | Required | Example |
|----------|----------|---------|
| `SENTRY_DSN` | **Yes** | `https://[key]@sentry.io/[id]` |
| `SENTRY_ENVIRONMENT` | No | `production` |
| `SENTRY_TRACES_SAMPLE_RATE` | No | `1.0` (100%) |
| `SENTRY_ENABLE_LOGS` | No | `true` |
| `SENTRY_LOG_BREADCRUMB_LEVEL` | No | `INFO` |
| `SENTRY_LOG_EVENT_LEVEL` | No | `ERROR` |

---

## 📊 Verifying It Works

### Datadog
```bash
# Check traces in Datadog APM
https://app.datadoghq.com/apm/services

# Generate test error
curl -X POST http://localhost:9000/api/v1/app-event/error?message=test

# Should appear in Datadog Events
```

### Sentry
```bash
# Check errors in Sentry dashboard
https://sentry.io/organizations/[org]/issues/

# Generate test error
curl -X POST http://localhost:9000/api/v1/app-event/error?message=test

# Should appear in Sentry Issues
```

---

## 🚨 Troubleshooting

### Provider Not Switching
```bash
# 1. Check environment variable
docker exec images-api env | grep OBSERVABILITY_PROVIDER

# 2. Restart container (provider initializes once at startup)
docker restart images-api

# 3. Verify via health endpoint
curl http://localhost:9000/health
```

### Sentry Not Receiving Events
```bash
# Check DSN is set
docker exec images-api env | grep SENTRY_DSN

# Enable debug mode
docker run ... -e SENTRY_DEBUG=true ...

# Check logs
docker logs images-api | grep -i sentry
```

### Datadog Agent Connection Failed
```bash
# Test agent connectivity
curl http://DD_AGENT_HOST:8126/info

# Check agent host from container
docker exec images-api ping DD_AGENT_HOST

# Verify environment
docker exec images-api env | grep DD_AGENT_HOST
```

---

## 📖 Full Documentation

See [OBSERVABILITY_PROVIDER_TOGGLE.md](docs/OBSERVABILITY_PROVIDER_TOGGLE.md) for:
- Complete architecture details
- Code integration examples
- Performance impact analysis
- Best practices
- Migration guide

---

**Last Updated**: 2025-01-11
