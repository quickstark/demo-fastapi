# SonarQube Integration Guide

This guide explains how SonarQube code analysis is integrated into the CI/CD pipeline.

## 📋 Prerequisites

1. **SonarQube Server**: You need access to a SonarQube server
2. **Project Token**: Generate a token in SonarQube for your project
3. **Project Key**: Already configured in `sonar-project.properties`

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# SonarQube Configuration
SONAR_TOKEN=your-sonarqube-token-here
SONAR_HOST_URL=https://your-sonarqube-server.com
```

### Upload Secrets to GitHub

```bash
# These will be uploaded automatically when you run:
./scripts/deploy.sh .env

# Or manually:
echo "your-token" | gh secret set SONAR_TOKEN
echo "https://your-sonarqube-url.com" | gh secret set SONAR_HOST_URL
```

## 📊 How It Works

### Automatic Analysis

SonarQube analysis runs automatically in both workflows:

1. **GitHub-Hosted Runner** (`deploy.yaml`)
   - Runs on manual trigger
   - Full analysis with all history

2. **Self-Hosted Runner** (`deploy-self-hosted.yaml`)
   - Runs on every push to main
   - Marked as `continue-on-error` to not block deployments

### What Gets Analyzed

Based on `sonar-project.properties`:
- **Sources**: `main.py`, `src/` directory
- **Tests**: `tests/` directory
- **Languages**: Python 3.9-3.12
- **Exclusions**: Cache files, virtual environments, test files

## 🎯 Quality Gate

The Quality Gate check is currently **commented out** in the workflows. To enforce it:

1. Uncomment these lines in `.github/workflows/deploy.yaml`:
   ```yaml
   - name: SonarQube Quality Gate check
     uses: SonarSource/sonarqube-quality-gate-action@v1
     timeout-minutes: 5
     env:
       SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
   ```

2. This will fail the build if code quality doesn't meet standards

## 📈 Viewing Results

After analysis completes:
1. Go to your SonarQube server
2. Find project: `quickstark_demo-fastapi`
3. View:
   - Code coverage
   - Bugs and vulnerabilities
   - Code smells
   - Security hotspots
   - Duplications

## 🔄 Adding Coverage Reports

To include test coverage in SonarQube:

1. Generate coverage report:
   ```bash
   pytest --cov=src --cov-report=xml
   ```

2. Uncomment in `sonar-project.properties`:
   ```properties
   sonar.python.coverage.reportPaths=coverage.xml
   ```

3. Update workflow to generate coverage before SonarQube scan

## 🚀 Local Analysis

To run SonarQube analysis locally:

```bash
# Install scanner
brew install sonar-scanner  # macOS
# or
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.8.0.2856-linux.zip

# Run analysis
sonar-scanner \
  -Dsonar.projectKey=quickstark_demo-fastapi_6ba235ba-ff96-459d-8607-919121b2ad98 \
  -Dsonar.sources=. \
  -Dsonar.host.url=$SONAR_HOST_URL \
  -Dsonar.login=$SONAR_TOKEN
```

## ⚠️ Troubleshooting

### Analysis Fails
- Check `SONAR_TOKEN` is valid
- Verify `SONAR_HOST_URL` is accessible
- Check project key in `sonar-project.properties`

### Missing Metrics
- Ensure source directories are correctly specified
- Check exclusion patterns aren't too broad
- Verify Python version compatibility

### Quality Gate Issues
- Review quality gate criteria in SonarQube
- Fix critical issues first
- Consider adjusting thresholds for new projects

## 📚 Best Practices

1. **Fix issues promptly**: Address new issues in each PR
2. **Monitor trends**: Track quality metrics over time
3. **Set realistic goals**: Gradually improve code quality
4. **Use PR decoration**: Enable GitHub PR comments (requires GitHub App)
5. **Regular reviews**: Review SonarQube reports in team meetings

## 🔗 Resources

- [SonarQube Documentation](https://docs.sonarqube.org/)
- [Python Analysis](https://docs.sonarqube.org/latest/analysis/languages/python/)
- [GitHub Integration](https://docs.sonarqube.org/latest/analysis/github-integration/)
