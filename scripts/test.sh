#!/bin/bash

# =============================================================================
# Test Runner Script with Datadog Test Optimization
# =============================================================================
# This script runs pytest with comprehensive Datadog CI Visibility integration
# Usage: ./scripts/test.sh [test-type] [pytest-args...]

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get to project root (script is in scripts/ subdirectory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${CYAN}🧪 Running tests with Datadog Test Optimization...${NC}"

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

echo -e "${BLUE}Environment Configuration:${NC}"
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
if [[ -z "$DD_API_KEY" ]]; then
    echo -e "${YELLOW}⚠️  Warning: No Datadog API key found. Tests will run without Datadog integration.${NC}"
    echo -e "${YELLOW}   Set DD_API_KEY environment variable to enable Datadog Test Optimization.${NC}"
    echo ""
fi

echo ""

# Check if we have the required dependencies
if ! python -c "import ddtrace" 2>/dev/null; then
    echo -e "${YELLOW}❌ ddtrace not found. Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Function to run pytest with or without ddtrace
run_pytest() {
    local test_args="$@"
    
    if command -v ddtrace-run &> /dev/null; then
        ddtrace-run pytest $test_args
    else
        echo -e "${YELLOW}⚠️  ddtrace-run not found. Running pytest without Datadog instrumentation.${NC}"
        pytest $test_args
    fi
}

# Show usage if help requested
show_usage() {
    echo -e "${CYAN}Usage: $0 [test-type] [pytest-args...]${NC}"
    echo ""
    echo -e "${BLUE}Test Types:${NC}"
    echo "  unit          - Run unit tests only"
    echo "  integration   - Run integration tests only"
    echo "  fast          - Run fast tests (excluding slow and mongo tests)"
    echo "  mongo         - Run MongoDB tests only"
    echo "  no-mongo      - Run all tests except MongoDB tests"
    echo "  all           - Run all tests (default)"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 unit -v"
    echo "  $0 fast --cov=src"
    echo "  $0 integration -x"
    echo "  $0 all --html=report.html"
    echo ""
}

# Run tests with different options based on arguments
case "${1:-all}" in
    "help"|"-h"|"--help")
        show_usage
        exit 0
        ;;
    "unit")
        echo -e "${GREEN}🏃 Running unit tests only...${NC}"
        run_pytest -m "unit" "${@:2}"
        ;;
    "integration")
        echo -e "${GREEN}🏃 Running integration tests only...${NC}"
        run_pytest -m "integration" "${@:2}"
        ;;
    "fast")
        echo -e "${GREEN}🏃 Running fast tests (excluding slow and mongo tests)...${NC}"
        run_pytest -m "not slow and not mongo" "${@:2}"
        ;;
    "mongo")
        echo -e "${GREEN}🏃 Running MongoDB tests only...${NC}"
        echo -e "${YELLOW}⚠️  Note: MongoDB tests require valid MONGO_CONN, MONGO_USER, and MONGO_PW environment variables${NC}"
        run_pytest -m "mongo" "${@:2}"
        ;;
    "no-mongo")
        echo -e "${GREEN}🏃 Running all tests except MongoDB tests...${NC}"
        run_pytest --ignore=tests/mongo_test.py "${@:2}"
        ;;
    "all"|*)
        echo -e "${GREEN}🏃 Running all tests...${NC}"
        run_pytest "${@:1}"
        ;;
esac

echo ""
echo -e "${GREEN}✅ Tests completed!${NC}"

# If running in CI, you can add additional reporting here
if [[ -n "$CI" ]]; then
    echo -e "${CYAN}📊 Test results should be visible in Datadog CI Visibility${NC}"
    echo -e "${CYAN}   View at: https://app.datadoghq.com/ci/test-runs${NC}"
fi 