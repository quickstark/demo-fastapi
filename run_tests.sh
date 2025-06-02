#!/bin/bash

# Test runner script with Datadog Test Optimization
# This script demonstrates how to run pytest with Datadog CI Visibility

set -e

echo "🧪 Running tests with Datadog Test Optimization..."

# Set environment variables for Datadog
export DD_ENV=${DD_ENV:-"test"}
export DD_SERVICE=${DD_SERVICE:-"images-api"}
export DD_VERSION=${DD_VERSION:-"local-$(date +%Y%m%d-%H%M%S)"}

# Enable Datadog CI Visibility
export DD_CIVISIBILITY_ENABLED=true

# Optional: Enable Test Impact Analysis (requires setup in Datadog)
export DD_CIVISIBILITY_ITR_ENABLED=${DD_CIVISIBILITY_ITR_ENABLED:-false}

# Set site if not already set
export DD_SITE=${DD_SITE:-"datadoghq.com"}

# Enable agentless mode for local testing (uses API key directly)
export DD_CIVISIBILITY_AGENTLESS_ENABLED=true

# Disable LLM Observability completely to avoid ragas dependency issues
export DD_LLMOBS_ENABLED=false
export DD_LLMOBS_EVALUATORS_ENABLED=false

# Set test environment variables for MongoDB (prevent connection errors during test collection)
export MONGO_CONN=${MONGO_CONN:-"localhost"}
export MONGO_USER=${MONGO_USER:-"testuser"}
export MONGO_PW=${MONGO_PW:-"testpass"}

echo "Environment Configuration:"
echo "  DD_ENV: $DD_ENV"
echo "  DD_SERVICE: $DD_SERVICE"
echo "  DD_VERSION: $DD_VERSION"
echo "  DD_CIVISIBILITY_ENABLED: $DD_CIVISIBILITY_ENABLED"
echo "  DD_CIVISIBILITY_ITR_ENABLED: $DD_CIVISIBILITY_ITR_ENABLED"
echo "  DD_SITE: $DD_SITE"
echo "  DD_CIVISIBILITY_AGENTLESS_ENABLED: $DD_CIVISIBILITY_AGENTLESS_ENABLED"
echo "  DD_LLMOBS_ENABLED: $DD_LLMOBS_ENABLED"
echo "  DD_LLMOBS_EVALUATORS_ENABLED: $DD_LLMOBS_EVALUATORS_ENABLED"

# Check if Datadog API key is set
if [[ -z "$DD_API_KEY" && -z "$DATADOG_API_KEY" ]]; then
    echo "⚠️  Warning: No Datadog API key found. Tests will run without Datadog integration."
    echo "   Set DD_API_KEY or DATADOG_API_KEY environment variable to enable Datadog Test Optimization."
    echo ""
fi

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
        if command -v ddtrace-run &> /dev/null; then
            ddtrace-run pytest -m "unit" "${@:2}"
        else
            echo "⚠️  ddtrace-run not found. Running pytest without Datadog instrumentation."
            pytest -m "unit" "${@:2}"
        fi
        ;;
    "integration")
        echo "🏃 Running integration tests only..."
        if command -v ddtrace-run &> /dev/null; then
            ddtrace-run pytest -m "integration" "${@:2}"
        else
            echo "⚠️  ddtrace-run not found. Running pytest without Datadog instrumentation."
            pytest -m "integration" "${@:2}"
        fi
        ;;
    "fast")
        echo "🏃 Running fast tests (excluding slow and mongo tests)..."
        if command -v ddtrace-run &> /dev/null; then
            ddtrace-run pytest -m "not slow and not mongo" "${@:2}"
        else
            echo "⚠️  ddtrace-run not found. Running pytest without Datadog instrumentation."
            pytest -m "not slow and not mongo" "${@:2}"
        fi
        ;;
    "mongo")
        echo "🏃 Running MongoDB tests only..."
        echo "⚠️  Note: MongoDB tests require valid MONGO_CONN, MONGO_USER, and MONGO_PW environment variables"
        if command -v ddtrace-run &> /dev/null; then
            ddtrace-run pytest -m "mongo" "${@:2}"
        else
            echo "⚠️  ddtrace-run not found. Running pytest without Datadog instrumentation."
            pytest -m "mongo" "${@:2}"
        fi
        ;;
    "no-mongo")
        echo "🏃 Running all tests except MongoDB tests..."
        if command -v ddtrace-run &> /dev/null; then
            ddtrace-run pytest --ignore=tests/mongo_test.py "${@:2}"
        else
            echo "⚠️  ddtrace-run not found. Running pytest without Datadog instrumentation."
            pytest --ignore=tests/mongo_test.py "${@:2}"
        fi
        ;;
    "all"|*)
        echo "🏃 Running all tests..."
        if command -v ddtrace-run &> /dev/null; then
            ddtrace-run pytest "${@:1}"
        else
            echo "⚠️  ddtrace-run not found. Running pytest without Datadog instrumentation."
            echo "   Install ddtrace with: pip install ddtrace"
            pytest "${@:1}"
        fi
        ;;
esac

echo ""
echo "✅ Tests completed!"

# If running in CI, you can add additional reporting here
if [[ -n "$CI" ]]; then
    echo "📊 Test results should be visible in Datadog CI Visibility"
    echo "   View at: https://app.datadoghq.com/ci/test-runs"
fi 