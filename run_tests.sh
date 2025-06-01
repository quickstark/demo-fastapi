#!/bin/bash

# Test runner script with Datadog integration
# This script runs pytest with Datadog Test Optimization enabled

set -e

echo "🧪 Running tests with Datadog Test Optimization..."

# Set environment variables for Datadog
export DD_ENV=${DD_ENV:-"test"}
export DD_SERVICE=${DD_SERVICE:-"images-api"}
export DD_VERSION=${DD_VERSION:-"local"}

# Enable Datadog CI Visibility
export DD_CIVISIBILITY_ENABLED=true

# Optional: Enable Test Impact Analysis (requires setup in Datadog)
export DD_CIVISIBILITY_ITR_ENABLED=${DD_CIVISIBILITY_ITR_ENABLED:-false}

# Set site if not already set
export DD_SITE=${DD_SITE:-"datadoghq.com"}

echo "Environment:"
echo "  DD_ENV: $DD_ENV"
echo "  DD_SERVICE: $DD_SERVICE"
echo "  DD_VERSION: $DD_VERSION"
echo "  DD_CIVISIBILITY_ENABLED: $DD_CIVISIBILITY_ENABLED"
echo "  DD_CIVISIBILITY_ITR_ENABLED: $DD_CIVISIBILITY_ITR_ENABLED"
echo ""

# Check if we have the required dependencies
if ! python -c "import ddtrace" 2>/dev/null; then
    echo "❌ ddtrace not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Run tests with different options based on arguments
case "${1:-all}" in
    "unit")
        echo "🏃 Running unit tests only..."
        DD_ENV=$DD_ENV DD_SERVICE=$DD_SERVICE pytest -m "unit" --ddtrace
        ;;
    "integration")
        echo "🏃 Running integration tests only..."
        DD_ENV=$DD_ENV DD_SERVICE=$DD_SERVICE pytest -m "integration" --ddtrace
        ;;
    "fast")
        echo "🏃 Running fast tests (excluding slow tests)..."
        DD_ENV=$DD_ENV DD_SERVICE=$DD_SERVICE pytest -m "not slow" --ddtrace
        ;;
    "mongo")
        echo "🏃 Running MongoDB tests only..."
        DD_ENV=$DD_ENV DD_SERVICE=$DD_SERVICE pytest -m "mongo" --ddtrace
        ;;
    "all"|*)
        echo "🏃 Running all tests..."
        DD_ENV=$DD_ENV DD_SERVICE=$DD_SERVICE pytest --ddtrace
        ;;
esac

echo ""
echo "✅ Tests completed!"
echo ""
echo "📊 View test results in Datadog:"
echo "   https://app.datadoghq.com/ci/test-runs" 