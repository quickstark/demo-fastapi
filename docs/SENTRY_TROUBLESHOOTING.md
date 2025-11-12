# Sentry Troubleshooting Guide

## Common Issue: Profiles and Logs Not Showing

### Symptoms
- ✅ Errors are captured in Sentry
- ✅ Traces/Performance monitoring works
- ❌ Profiles don't appear
- ❌ Logs don't show up in Logs UI

### Most Common Causes

#### 1. **Old Container Running (Most Likely!)**

If you deployed **before** the recent fixes, your container has:
- ❌ `SENTRY_PROFILES_SAMPLE_RATE="0.0"` (profiling disabled)
- ❌ `profile_lifecycle` bug (invalid parameter)
- ❌ No structured logging calls

**Solution:** Redeploy with the latest code!

```bash
# Rebuild and deploy
./scripts/deploy.sh

# OR for local testing
./scripts/build.sh --env-file .env --run
```

#### 2. **Environment Variables Not Set**

Check your `.env` file has:

```bash
# Required for Sentry
OBSERVABILITY_PROVIDER=sentry
SENTRY_DSN=https://your-dsn@sentry.io/project-id

# Required for profiling (must be > 0)
SENTRY_PROFILES_SAMPLE_RATE=1.0

# Required for logs
SENTRY_ENABLE_LOGS=true
SENTRY_LOG_BREADCRUMB_LEVEL=INFO
SENTRY_LOG_EVENT_LEVEL=ERROR
```

#### 3. **Profiling Requires CPU Work**

Profiles only capture when there's actual CPU-intensive work during a traced transaction.

**Test with a CPU-intensive endpoint:**

```bash
# This endpoint does actual work that can be profiled
curl http://localhost:8080/add_image -F "file=@test-image.jpg"
```

Simple endpoints like `/health` won't generate interesting profiles.

#### 4. **Logs Require Structured Logging Calls**

The recent code changes added `sentry_sdk.logger` calls. If your container is old, it won't have these.

**After redeploying, test:**

```bash
curl http://localhost:8080/test-sentry-logs
```

## Diagnostic Steps

### Step 1: Check Container Configuration

Hit the diagnostic endpoint on your **running container**:

```bash
curl http://your-container:8080/sentry-diagnostics | jq
```

**Look for:**
- `SENTRY_PROFILES_SAMPLE_RATE` should be `"1.0"` (not `"0.0"`)
- `SENTRY_ENABLE_LOGS` should be `"true"` (not `"false"`)
- `OBSERVABILITY_PROVIDER` should be `"sentry"`
- `sentry_options.profiles_sample_rate` should be `1.0` (numeric)
- `integrations` should include `LoggingIntegration`, `FastAPIIntegration`, etc.

**Example Good Output:**
```json
{
  "environment_variables": {
    "OBSERVABILITY_PROVIDER": "sentry",
    "SENTRY_PROFILES_SAMPLE_RATE": "1.0",
    "SENTRY_ENABLE_LOGS": "true"
  },
  "sentry_options": {
    "traces_sample_rate": 1.0,
    "profiles_sample_rate": 1.0,
    "integrations": [
      "FastAPIIntegration",
      "StarletteIntegration", 
      "HttpxIntegration",
      "LoggingIntegration"
    ]
  },
  "profiling_support": "GeventScheduler available",
  "structured_logging": "Available",
  "recommendations": [
    "✅ Configuration looks good!"
  ]
}
```

**Example Bad Output (Old Container):**
```json
{
  "environment_variables": {
    "SENTRY_PROFILES_SAMPLE_RATE": "0.0",  // ❌ DISABLED!
    "SENTRY_ENABLE_LOGS": "NOT SET"        // ❌ MISSING!
  },
  "recommendations": [
    "⚠️ SENTRY_PROFILES_SAMPLE_RATE is 0.0 or not set - profiling is disabled!",
    "⚠️ SENTRY_ENABLE_LOGS is false or not set - logs may not be captured!"
  ]
}
```

### Step 2: Test Structured Logging

```bash
# This should create 3 logs in Sentry's Logs UI
curl http://your-container:8080/test-sentry-logs

# Expected response
{
  "message": "Sentry test logs sent",
  "logs_sent": 3,
  "levels": ["debug", "info", "warning"],
  "provider": "sentry",
  "provider_enabled": true
}
```

### Step 3: Generate Traffic for Profiles

Profiles need CPU work. Upload an image:

```bash
curl -X POST http://your-container:8080/add_image \
  -F "file=@test-image.jpg" \
  -F "backend=mongo"
```

This triggers:
- S3 upload (I/O)
- Rekognition analysis (CPU)
- Database insertion (I/O)
- Multiple logs and traces

### Step 4: Check Sentry UI

#### For Logs:
1. Go to Sentry → **Logs** (left sidebar)
2. Wait 30-60 seconds for ingestion
3. Filter: `operation:test_logging`
4. Should see 3 log entries with structured fields

#### For Profiles:
1. Go to Sentry → **Performance** → **Profiles**
2. Wait 1-2 minutes for processing
3. Look for `/add_image` transactions
4. Should see flamegraph with function call stacks

## Known Limitations

### Profiling
- **Requires actual CPU work**: Simple endpoints won't generate profiles
- **Platform-specific**: Works best on Linux x64 (your container)
- **Sampling overhead**: Set `SENTRY_PROFILES_SAMPLE_RATE=0.1` in production
- **Processing delay**: Profiles take 1-2 minutes to appear in UI

### Logs
- **Must use `sentry_sdk.logger`**: Standard Python `logging` only creates breadcrumbs
- **Ingestion delay**: 30-60 seconds
- **Filtering**: Check log level filters in Sentry UI (don't filter out INFO/DEBUG)

## Quick Fixes

### "Profiling Not Working"

```bash
# 1. Check your .env file
grep SENTRY_PROFILES_SAMPLE_RATE .env
# Should output: SENTRY_PROFILES_SAMPLE_RATE=1.0

# 2. Redeploy (most likely fix!)
./scripts/deploy.sh

# 3. Check diagnostics after deploy
curl http://your-container:8080/sentry-diagnostics | jq '.environment_variables.SENTRY_PROFILES_SAMPLE_RATE'
# Should output: "1.0"
```

### "Logs Not Working"

```bash
# 1. Check your .env file
grep SENTRY_ENABLE_LOGS .env
# Should output: SENTRY_ENABLE_LOGS=true

# 2. Verify structured logging is available
curl http://your-container:8080/sentry-diagnostics | jq '.structured_logging'
# Should output: "Available"

# 3. Test logging
curl http://your-container:8080/test-sentry-logs

# 4. Check Sentry UI (wait 60 seconds)
# Go to Logs → filter by: operation:test_logging
```

## Still Not Working?

### Enable Debug Mode

Add to your `.env`:
```bash
SENTRY_DEBUG=true
```

Redeploy and check container logs for Sentry output:
```bash
docker logs <container-name> 2>&1 | grep -i sentry
```

### Check Sentry Rate Limits

Your Sentry plan might have:
- Transaction/event limits
- Profile quotas
- Log ingestion limits

Check: Sentry → Settings → Subscription → Usage

### Verify SDK Version

```bash
curl http://your-container:8080/sentry-diagnostics | jq '.sentry_sdk_version'
```

Should be `>= 2.44.0` (you have this ✅)

## Summary Checklist

Before opening a support ticket:

- [ ] Redeployed with latest code (after recent fixes)
- [ ] `.env` has `SENTRY_PROFILES_SAMPLE_RATE=1.0`
- [ ] `.env` has `SENTRY_ENABLE_LOGS=true`
- [ ] Diagnostic endpoint shows good config
- [ ] Test logs endpoint returns success
- [ ] Generated CPU-intensive traffic (image upload)
- [ ] Waited 2-3 minutes for Sentry ingestion
- [ ] Checked Sentry UI filters (not filtering out your logs)
- [ ] Verified Sentry plan limits not exceeded

