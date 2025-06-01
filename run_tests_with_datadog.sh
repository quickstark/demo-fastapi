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

echo "Environment Configuration:"
echo "  DD_ENV: $DD_ENV"
echo "  DD_SERVICE: $DD_SERVICE"
echo "  DD_VERSION: $DD_VERSION"
echo "  DD_CIVISIBILITY_ENABLED: $DD_CIVISIBILITY_ENABLED"
echo "  DD_CIVISIBILITY_ITR_ENABLED: $DD_CIVISIBILITY_ITR_ENABLED"
echo "  DD_SITE: $DD_SITE"
echo "  DD_CIVISIBILITY_AGENTLESS_ENABLED: $DD_CIVISIBILITY_AGENTLESS_ENABLED"

# Check if Datadog API key is set
if [[ -z "$DD_API_KEY" && -z "$DATADOG_API_KEY" ]]; then
    echo "⚠️  Warning: No Datadog API key found. Tests will run without Datadog integration."
    echo "   Set DD_API_KEY or DATADOG_API_KEY environment variable to enable Datadog Test Optimization."
    echo ""
fi

echo ""
echo "🚀 Running pytest with ddtrace..."

# Run pytest with ddtrace for Datadog integration
# The ddtrace-run command automatically instruments pytest
if command -v ddtrace-run &> /dev/null; then
    ddtrace-run pytest "$@"
else
    echo "⚠️  ddtrace-run not found. Running pytest without Datadog instrumentation."
    echo "   Install ddtrace with: pip install ddtrace"
    pytest "$@"
fi

echo ""
echo "✅ Tests completed!"

# If running in CI, you can add additional reporting here
if [[ -n "$CI" ]]; then
    echo "📊 Test results should be visible in Datadog CI Visibility"
    echo "   View at: https://app.datadoghq.com/ci/test-runs"
fi 