# Datadog Test Optimization Setup

This document explains how to set up and use Datadog Test Optimization with pytest in this FastAPI project.

## Overview

Datadog Test Optimization provides:

- **Test Visibility**: Track test performance, flaky tests, and failure rates
- **Test Impact Analysis**: Run only tests affected by code changes
- **CI/CD Integration**: Correlate test results with deployments and performance
- **Intelligent Test Selection**: Skip tests that aren't impacted by changes

## Setup

### 1. Dependencies

The following packages are required (already in `requirements.txt`):

```bash
pytest==7.4.3
pytest-asyncio==0.21.1
ddtrace==2.14.0  # Datadog tracing library
```

### 2. Environment Variables

Set these environment variables for Datadog integration:

```bash
# Required for Datadog Test Optimization
DD_API_KEY=your_datadog_api_key
DD_SITE=datadoghq.com

# Test configuration
DD_ENV=test                    # Environment name (test, staging, prod)
DD_SERVICE=images-api          # Service name
DD_VERSION=1.0.0              # Version/commit hash

# CI Visibility settings
DD_CIVISIBILITY_ENABLED=true
DD_CIVISIBILITY_AGENTLESS_ENABLED=true  # For local testing
DD_CIVISIBILITY_ITR_ENABLED=false      # Test Impact Analysis (optional)
```

### 3. Test Configuration

The `pytest.ini` file is configured with:

- **Async support**: `asyncio_mode = auto`
- **Custom markers**: `unit`, `integration`, `slow`, `mongo`, `postgres`, `api`
- **Output formatting**: Verbose output with colors

## Running Tests

### Local Development

#### Option 1: Simple pytest (no Datadog)
```bash
pytest tests/ -v
```

#### Option 2: With Datadog Integration
```bash
# Set your API key first
export DD_API_KEY=your_datadog_api_key

# Run with Datadog integration
./run_tests_with_datadog.sh tests/
```

#### Option 3: Manual ddtrace integration
```bash
export DD_API_KEY=your_datadog_api_key
export DD_CIVISIBILITY_ENABLED=true
ddtrace-run pytest tests/ -v
```

### GitHub Actions

The GitHub Actions workflow automatically runs tests with Datadog integration:

```yaml
- name: Configure Datadog Test Optimization
  uses: datadog/test-visibility-github-action@v2
  with:
    languages: python
    api_key: ${{ secrets.DATADOG_API_KEY }}
    site: datadoghq.com

- name: Run Tests with Datadog
  run: |
    export DD_ENV="ci"
    export DD_SERVICE="images-api"
    export DD_VERSION="${{ github.sha }}"
    ddtrace-run pytest tests/ -v --junitxml=test-results.xml
```

## Test Organization

### Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit`: Fast unit tests, no external dependencies
- `@pytest.mark.integration`: Tests requiring external services
- `@pytest.mark.slow`: Tests taking >1 second
- `@pytest.mark.mongo`: Tests requiring MongoDB
- `@pytest.mark.postgres`: Tests requiring PostgreSQL
- `@pytest.mark.api`: API endpoint tests

### Example Usage

```python
import pytest

@pytest.mark.unit
def test_basic_functionality():
    assert 1 + 1 == 2

@pytest.mark.integration
@pytest.mark.mongo
async def test_database_operation():
    # Test that requires MongoDB
    pass

@pytest.mark.slow
@pytest.mark.api
def test_api_endpoint():
    # Slow API test
    pass
```

### Running Specific Test Types

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run everything except slow tests
pytest -m "not slow"

# Run MongoDB tests only
pytest -m mongo
```

## Test Files

### Current Test Structure

```
tests/
├── conftest.py           # Pytest configuration and fixtures
├── test_simple.py        # Simple unit tests (no dependencies)
├── test_basic.py         # FastAPI endpoint tests
└── mongo_test.py         # MongoDB integration tests
```

### Test File Examples

#### Simple Unit Tests (`test_simple.py`)
- Basic math operations
- String/list/dict operations
- Environment variable access
- No external dependencies

#### API Tests (`test_basic.py`)
- FastAPI endpoint testing
- Uses TestClient
- Health checks and basic routes

#### Integration Tests (`mongo_test.py`)
- MongoDB connection tests
- Database operations
- Requires MongoDB credentials

## Datadog Test Visibility Features

### 1. Test Performance Tracking
- Test execution times
- Performance trends over time
- Slowest tests identification

### 2. Flaky Test Detection
- Tests that pass/fail inconsistently
- Failure rate tracking
- Root cause analysis

### 3. Test Impact Analysis
- Skip tests unaffected by code changes
- Faster CI/CD pipelines
- Intelligent test selection

### 4. CI/CD Correlation
- Link test results to deployments
- Performance impact analysis
- Rollback decision support

## Viewing Results

### Datadog Dashboard

After running tests with Datadog integration:

1. Go to [Datadog CI Visibility](https://app.datadoghq.com/ci/test-runs)
2. Filter by service: `images-api`
3. View test results, performance, and trends

### Key Metrics to Monitor

- **Test Success Rate**: Overall pass/fail percentage
- **Test Duration**: Average and P95 test execution times
- **Flaky Tests**: Tests with inconsistent results
- **Coverage**: Code coverage percentage (if configured)

## Troubleshooting

### Common Issues

#### 1. ddtrace not found
```bash
pip install ddtrace
```

#### 2. API key not set
```bash
export DD_API_KEY=your_datadog_api_key
```

#### 3. Tests not appearing in Datadog
- Verify `DD_CIVISIBILITY_ENABLED=true`
- Check API key is correct
- Ensure `DD_SITE` matches your Datadog instance

#### 4. Import errors in tests
- Install missing dependencies
- Check Python path configuration
- Verify virtual environment activation

### Debug Mode

Enable debug logging:

```bash
export DD_TRACE_DEBUG=true
export DD_LOGS_INJECTION=true
ddtrace-run pytest tests/ -v
```

## Best Practices

### 1. Test Organization
- Use descriptive test names
- Group related tests in classes
- Use appropriate markers
- Keep tests independent

### 2. Performance
- Mark slow tests with `@pytest.mark.slow`
- Use fixtures for expensive setup
- Mock external dependencies in unit tests

### 3. CI/CD Integration
- Run fast tests first
- Use Test Impact Analysis in CI
- Set appropriate timeouts
- Generate test reports

### 4. Monitoring
- Set up alerts for test failures
- Monitor test performance trends
- Track flaky test rates
- Review coverage reports

## Next Steps

1. **Enable Test Impact Analysis**: Set `DD_CIVISIBILITY_ITR_ENABLED=true` after initial setup
2. **Add More Tests**: Expand test coverage for critical paths
3. **Set Up Alerts**: Configure Datadog alerts for test failures
4. **Performance Monitoring**: Track test performance over time
5. **Code Coverage**: Integrate coverage reporting with Datadog

## Resources

- [Datadog Test Optimization Documentation](https://docs.datadoghq.com/tests/)
- [Python Test Instrumentation](https://docs.datadoghq.com/tests/setup/python/)
- [CI Visibility](https://docs.datadoghq.com/continuous_integration/)
- [Test Impact Analysis](https://docs.datadoghq.com/tests/test_impact_analysis/) 