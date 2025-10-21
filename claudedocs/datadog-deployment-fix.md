# Fixing Datadog Deployment Tracking

## Problem Identified

**Status**: Your deployment is working, but Datadog deployment marking is **silently failing**.

**Evidence from logs**:
```
⚠️  Datadog CI not available, skipping deployment marking
✅ Deployment marked in Datadog with version 2.0.1
```

The "✅" message is misleading - it actually **skipped** the marking!

## Root Cause

1. `datadog-ci` is **not installed** on your self-hosted runner
2. `npm` is not available (or npm install failed)
3. The workflow step has `continue-on-error: true`, so it passes even when failing

## What You're Seeing vs What You Need

### Currently Seeing (CI Pipeline Executions)
- ✅ Automatically tracked by GitHub Actions integration
- ✅ Shows in Datadog as "CI Pipeline Executions"
- ❌ Uses commit SHAs (ae5428f, 57343e8) instead of semantic versions
- ❌ Not the same as "Deployment Tracking"

### What You Need (Deployment Tracking)
- ❌ Requires `datadog-ci deployment mark` command
- ❌ Shows semantic versions (2.0.1) in Datadog CD view
- ❌ Currently failing silently
- ✅ **This is what we're fixing**

---

## Solutions (Choose One)

### Option 1: Install datadog-ci on Self-Hosted Runner (Recommended)

**Step 1: SSH into your self-hosted runner**
```bash
ssh user@your-runner-host
```

**Step 2: Install Node.js and npm (if not already installed)**

For **Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install -y nodejs npm
```

For **macOS**:
```bash
brew install node
```

For **RHEL/CentOS**:
```bash
sudo yum install -y nodejs npm
```

**Step 3: Install datadog-ci globally**
```bash
sudo npm install -g @datadog/datadog-ci
```

**Step 4: Verify installation**
```bash
datadog-ci version
# Should output: X.X.X
```

**Step 5: Trigger a new deployment**
```bash
# On your local machine
git commit --allow-empty -m "Test Datadog deployment marking"
git push origin main
```

**Step 6: Check workflow logs**
Look for:
```
✓ Found datadog-ci in PATH
✅ Deployment marked successfully with datadog-ci
🎉 Deployment successfully marked in Datadog with version X.X.X
```

---

### Option 2: Use HTTP API Instead of datadog-ci

If you can't install datadog-ci, you can use Datadog's HTTP API directly with `curl`.

**Add this alternative step to your workflow:**

```yaml
- name: Mark Deployment via HTTP API
  if: success()
  continue-on-error: true
  run: |
    VERSION="${{ steps.version.outputs.version }}"
    SHORT_SHA="${{ github.sha }}"
    SHORT_SHA="${SHORT_SHA:0:7}"

    curl -X POST "https://api.datadoghq.com/api/v1/events" \
      -H "Content-Type: application/json" \
      -H "DD-API-KEY: ${{ secrets.DD_API_KEY }}" \
      -d @- <<EOF
    {
      "title": "Deployment: ${{ secrets.DD_SERVICE }} v${VERSION}",
      "text": "Deployed version ${VERSION} to ${{ secrets.DD_ENV }} environment",
      "tags": [
        "service:${{ secrets.DD_SERVICE }}",
        "env:${{ secrets.DD_ENV }}",
        "version:${VERSION}",
        "deployment_method:self_hosted",
        "git_sha:${SHORT_SHA}",
        "repository:${{ github.repository }}",
        "branch:${{ github.ref_name }}"
      ],
      "alert_type": "info"
    }
    EOF

    echo "✅ Deployment event sent to Datadog"
```

**Note**: This creates a Datadog Event, which is slightly different from the official deployment tracking but will show up in the Events stream.

---

### Option 3: Install npm on Self-Hosted Runner

If npm installation failed in the workflow, you can ensure npm is available:

```bash
# SSH into self-hosted runner
ssh user@your-runner-host

# Install npm
sudo apt install -y npm  # Ubuntu/Debian
# or
brew install node  # macOS

# Verify
npm --version
```

Then the workflow will automatically install datadog-ci locally on each run.

---

## Updated Workflow Benefits

I've updated the workflow to provide **much better diagnostics**:

### New Features:
1. ✅ **Checks DD_API_KEY** is set before attempting
2. ✅ **Clearer logging** shows exactly what's happening
3. ✅ **Better error messages** explain how to fix issues
4. ✅ **Success tracking** only shows "✅" when actually successful
5. ✅ **Troubleshooting hints** printed in logs

### Next Deployment Will Show:
```
📦 Marking deployment with version: 2.0.1
🔖 Git SHA: 6a100d3

✓ Found datadog-ci in PATH
✅ Deployment marked successfully with datadog-ci

🎉 Deployment successfully marked in Datadog with version 2.0.1
```

**OR if it fails**:
```
❌ Neither datadog-ci nor npm is available

⚠️  WARNING: Deployment was NOT marked in Datadog
To fix this issue:
1. Install datadog-ci globally on self-hosted runner:
   sudo npm install -g @datadog/datadog-ci
2. Or install npm if not available
3. Verify DD_API_KEY secret is configured
```

---

## Verification Checklist

After installing datadog-ci, verify everything is working:

### 1. Check datadog-ci Installation
```bash
# On self-hosted runner
datadog-ci version
# Expected: X.X.X (e.g., 2.40.0)
```

### 2. Check DD_API_KEY Secret
- Go to GitHub repo → Settings → Secrets
- Verify `DD_API_KEY` is set
- Verify `DD_SERVICE` is set
- Verify `DD_ENV` is set

### 3. Trigger Test Deployment
```bash
# Update VERSION
echo "2.0.2" > VERSION
git add VERSION
git commit -m "Bump version to 2.0.2 - Test Datadog marking"
git push origin main
```

### 4. Check Workflow Logs
- Go to GitHub Actions
- Open the latest "Build and Deploy (Self-Hosted Runner)" workflow
- Look for "Mark Deployment in Datadog" step
- Verify it shows: "🎉 Deployment successfully marked..."

### 5. Check Datadog CD View
- Go to Datadog → APM → Service Catalog
- Select your service
- Click "Deployments" tab
- **Look for version 2.0.2** (not commit SHA!)
- Verify it shows recent timestamp

### 6. Verify Application Version
```bash
curl http://localhost:9000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "your-service",
  "version": "2.0.2",
  "environment": "production"
}
```

---

## Troubleshooting

### Issue: "❌ ERROR: DD_API_KEY is not set in secrets"

**Solution**:
1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Add secret: `DD_API_KEY` with your Datadog API key
3. Get API key from: Datadog → Organization Settings → API Keys

### Issue: "❌ Neither datadog-ci nor npm is available"

**Solution**:
- Install Node.js and npm on self-hosted runner (see Option 1 above)
- Or use HTTP API approach (see Option 2 above)

### Issue: Deployment shows in Datadog but wrong environment

**Solution**:
- Check `DD_ENV` secret matches the environment filter in Datadog
- If DD_ENV is "production" but you're viewing "dev" in Datadog, nothing will show
- Change environment filter in Datadog UI to match DD_ENV

### Issue: datadog-ci command fails with authentication error

**Solution**:
1. Verify DD_API_KEY is correct
2. Check if your Datadog site is correct (default: datadoghq.com)
3. If using EU site, you may need to set `DD_SITE` environment variable

---

## Expected Timeline

Once you install datadog-ci:

1. **Immediate** (< 1 min): datadog-ci available in runner
2. **Next deployment** (< 5 min): Workflow will mark deployment successfully
3. **Datadog ingestion** (1-2 min): Deployment appears in Datadog CD view
4. **Full visibility** (< 10 min total): Version tracking fully operational

---

## Summary

**Current Status**:
- ✅ VERSION file working
- ✅ Git tags creating
- ✅ GitHub Releases creating
- ✅ Semantic versioning implemented
- ✅ Workflow using correct version
- ❌ Datadog deployment marking failing (datadog-ci not installed)

**Next Action**:
**Install datadog-ci on self-hosted runner** (see Option 1 above)

**After Fix**:
- ✅ Datadog CD will show semantic versions
- ✅ Deployment tracking will work properly
- ✅ Version correlation across all systems
- ✅ Complete deployment visibility

---

## Additional Notes

### Why CI Pipeline Executions Show But Not Deployments

Datadog has **two separate features**:

1. **CI Visibility** (what you're seeing):
   - Automatically ingests from GitHub Actions
   - Shows pipeline executions
   - Uses metadata from GitHub (commit SHAs)
   - No configuration needed

2. **Deployment Tracking** (what we're fixing):
   - Requires explicit marking via datadog-ci
   - Shows semantic versions
   - Tracks deployment progression
   - **Needs datadog-ci to work**

### Why the Old Workflow Worked

The GitHub-hosted workflow (deploy.yaml) works because:
- It has a step that installs datadog-ci: `npm install -g @datadog/datadog-ci`
- GitHub-hosted runners have npm pre-installed
- The installation succeeds every time

The self-hosted runner workflow assumes these tools are available, but they're not installed by default on self-hosted runners.

---

**Questions?**

If you encounter any issues after following these steps, check:
1. Workflow logs for the exact error message
2. datadog-ci installation: `datadog-ci version`
3. GitHub secrets configuration
4. Datadog environment filter matches DD_ENV secret
