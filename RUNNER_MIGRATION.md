# Migration Guide: Current Runner to New Setup

This guide helps you migrate from your current GitHub runner (container ID: 5d543b71da4e) to the new optimized setup.

## 🔄 Migration Steps

### Step 1: Stop Current Runner
```bash
# Stop your existing runner
docker stop 5d543b71da4e

# Optional: Remove it (after confirming new runner works)
docker rm 5d543b71da4e
```

### Step 2: Prepare Environment File
```bash
# Copy the example environment file
cp runner.env.example .env.runner

# Get your current GitHub token from your existing setup
docker inspect 5d543b71da4e | grep ACCESS_TOKEN

# Edit .env.runner and add your token
nano .env.runner
# or
vim .env.runner
```

Replace `GITHUB_ACCESS_TOKEN=github_pat_your_token_here` with your actual token.

### Step 3: Verify Docker Group ID
```bash
# Your GMKTec Docker group ID is 988
# Verify it's correctly set in .env.runner
grep DOCKER_GROUP_ID .env.runner

# Should show: DOCKER_GROUP_ID=988
# If not, update it:
sed -i 's/DOCKER_GROUP_ID=.*/DOCKER_GROUP_ID=988/' .env.runner
```

### Step 4: Start New Runner
```bash
# Using the setup script (recommended)
./scripts/setup-runner.sh start

# Or using docker-compose directly
docker-compose -f docker-compose.runner.yml --env-file .env.runner up -d
```

### Step 5: Verify Runner Registration
1. Check runner logs:
   ```bash
   docker-compose -f docker-compose.runner.yml logs -f runner
   ```
   Look for "Connected to GitHub" or similar success message.

2. Check GitHub:
   - Go to: https://github.com/quickstark/demo-fastapi/settings/actions/runners
   - You should see a runner with status "Idle" or "Active"

### Step 6: Test Docker Access
```bash
# Test that the runner can access Docker
./scripts/setup-runner.sh test

# Or manually
docker-compose -f docker-compose.runner.yml exec runner docker ps
```

### Step 7: Test Deployment
Make a small change and push to main branch:
```bash
# Make a test change
echo "# Test deployment" >> README.md
git add README.md
git commit -m "Test: self-hosted runner deployment"
git push origin main
```

Watch the workflow at: https://github.com/quickstark/demo-fastapi/actions

### Step 8: Verify Application
After deployment completes:
```bash
# Check if container is running
docker ps | grep images-api

# Test the API
curl http://localhost:9000/health

# Check logs
docker logs images-api
```

## ✅ Success Indicators

You'll know the migration is successful when:
1. ✅ New runner appears in GitHub settings
2. ✅ Push to main triggers the workflow automatically
3. ✅ Workflow uses "self-hosted" runner (not GitHub-hosted)
4. ✅ Application deploys and runs on port 9000
5. ✅ Health endpoint responds successfully

## 🔙 Rollback Plan

If something goes wrong:

### Option 1: Restart Old Runner
```bash
# Stop new runner
docker-compose -f docker-compose.runner.yml down

# Restart old runner
docker start 5d543b71da4e
```

### Option 2: Use GitHub-Hosted Runner
```bash
# Manually trigger the backup workflow
gh workflow run deploy.yaml
# Or use GitHub UI: Actions → Build and Deploy (GitHub-Hosted) → Run workflow
```

## 📝 Key Differences from Old Setup

| Aspect | Old Setup | New Setup |
|--------|-----------|-----------|
| Management | Manual Docker commands | Setup script + docker-compose |
| Volumes | Unknown | Properly configured with cache |
| Docker Access | May not have socket mount | Guaranteed Docker socket access |
| Updates | Manual | `./scripts/setup-runner.sh update` |
| Logs | `docker logs` | `./scripts/setup-runner.sh logs` |
| Deployment | Unknown | Automatic to port 9000 |

## 🛠️ Ongoing Management

After migration, use the setup script for all management:
```bash
./scripts/setup-runner.sh status  # Check status
./scripts/setup-runner.sh logs    # View logs
./scripts/setup-runner.sh restart # Restart runner
./scripts/setup-runner.sh update  # Update runner image
```

## ⚠️ Important Notes

1. **Keep old runner stopped** during migration to avoid conflicts
2. **Don't delete old runner** until you confirm new setup works
3. **Token is the same** - you're using the same GitHub PAT
4. **Port 9000** is now the standard deployment port
5. **Automatic deployment** happens on every push to main

## 🆘 Troubleshooting

If runner doesn't appear in GitHub:
```bash
# Check token in env file
grep ACCESS_TOKEN .env.runner

# Check runner logs for errors
docker-compose -f docker-compose.runner.yml logs runner | grep -i error

# Verify Docker socket
docker-compose -f docker-compose.runner.yml exec runner ls -la /var/run/docker.sock
```

If deployment fails:
```bash
# Check workflow logs in GitHub Actions UI
# Check local Docker
docker ps -a | grep images-api
docker logs images-api
```

## 📞 Need Help?

If you encounter issues:
1. Check the full setup guide: [RUNNER_SETUP.md](RUNNER_SETUP.md)
2. Review workflow logs at: https://github.com/quickstark/demo-fastapi/actions
3. Check runner logs: `./scripts/setup-runner.sh logs`
