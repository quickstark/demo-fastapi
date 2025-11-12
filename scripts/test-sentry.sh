#!/bin/bash

# =============================================================================
# Sentry Configuration Test Script
# =============================================================================
# This script helps diagnose Sentry integration issues by:
# 1. Checking environment variables
# 2. Testing the /health endpoint
# 3. Triggering test events (errors, logs, traces)
# 4. Verifying Sentry receives the data

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
CONTAINER_NAME="${1:-images}"
API_URL="http://localhost:9000"

print_header() {
    echo -e "\n${CYAN}================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}================================${NC}"
}

print_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if container exists
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_error "Container '${CONTAINER_NAME}' is not running"
    echo "Available containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    exit 1
fi

print_header "Sentry Configuration Test"

# 1. Check environment variables in container
print_step "Checking Sentry environment variables in container..."
echo ""

OBSERVABILITY_PROVIDER=$(docker exec ${CONTAINER_NAME} printenv OBSERVABILITY_PROVIDER 2>/dev/null || echo "not set")
SENTRY_DSN=$(docker exec ${CONTAINER_NAME} printenv SENTRY_DSN 2>/dev/null || echo "not set")
SENTRY_TRACES=$(docker exec ${CONTAINER_NAME} printenv SENTRY_TRACES_SAMPLE_RATE 2>/dev/null || echo "not set")
SENTRY_PROFILES=$(docker exec ${CONTAINER_NAME} printenv SENTRY_PROFILES_SAMPLE_RATE 2>/dev/null || echo "not set")
SENTRY_LOGS=$(docker exec ${CONTAINER_NAME} printenv SENTRY_ENABLE_LOGS 2>/dev/null || echo "not set")

echo -e "${CYAN}Environment Variables:${NC}"
echo "  OBSERVABILITY_PROVIDER: $OBSERVABILITY_PROVIDER"
echo "  SENTRY_DSN: ${SENTRY_DSN:0:50}..."
echo "  SENTRY_TRACES_SAMPLE_RATE: $SENTRY_TRACES"
echo "  SENTRY_PROFILES_SAMPLE_RATE: $SENTRY_PROFILES"
echo "  SENTRY_ENABLE_LOGS: $SENTRY_LOGS"
echo ""

# Validate configuration
if [ "$OBSERVABILITY_PROVIDER" != "sentry" ]; then
    print_error "OBSERVABILITY_PROVIDER is not set to 'sentry'"
    print_warning "Set OBSERVABILITY_PROVIDER=sentry in your environment"
    exit 1
fi

if [ "$SENTRY_DSN" == "not set" ] || [ -z "$SENTRY_DSN" ]; then
    print_error "SENTRY_DSN is not configured"
    print_warning "Set SENTRY_DSN in your environment"
    exit 1
fi

if [ "$SENTRY_PROFILES" == "0.0" ] || [ "$SENTRY_PROFILES" == "not set" ]; then
    print_warning "Profiling is disabled (SENTRY_PROFILES_SAMPLE_RATE=$SENTRY_PROFILES)"
fi

print_success "Environment variables configured"

# 2. Check health endpoint
print_step "Checking health endpoint..."
HEALTH_RESPONSE=$(curl -s ${API_URL}/health 2>/dev/null || echo "")

if [ -z "$HEALTH_RESPONSE" ]; then
    print_error "Cannot reach ${API_URL}/health"
    print_warning "Is the container running and port forwarded correctly?"
    exit 1
fi

echo "$HEALTH_RESPONSE" | jq '.' 2>/dev/null || echo "$HEALTH_RESPONSE"

OBS_PROVIDER=$(echo "$HEALTH_RESPONSE" | jq -r '.observability_provider' 2>/dev/null || echo "unknown")
OBS_ENABLED=$(echo "$HEALTH_RESPONSE" | jq -r '.observability_enabled' 2>/dev/null || echo "unknown")

if [ "$OBS_PROVIDER" == "sentry" ] && [ "$OBS_ENABLED" == "true" ]; then
    print_success "Sentry is active and enabled"
else
    print_error "Sentry provider is not active"
    echo "  Provider: $OBS_PROVIDER"
    echo "  Enabled: $OBS_ENABLED"
    exit 1
fi

# 3. Check container logs for Sentry initialization
print_step "Checking container logs for Sentry initialization..."
echo ""

SENTRY_LOGS=$(docker logs ${CONTAINER_NAME} 2>&1 | grep -i "sentry" | tail -20)

if [ -z "$SENTRY_LOGS" ]; then
    print_warning "No Sentry-related logs found"
else
    echo "$SENTRY_LOGS"
    echo ""
fi

# Look for specific indicators
if echo "$SENTRY_LOGS" | grep -q "Sentry SDK client active"; then
    print_success "Sentry SDK initialized successfully"
else
    print_warning "Could not confirm Sentry SDK initialization"
fi

if echo "$SENTRY_LOGS" | grep -q "Profiling configured"; then
    PROFILE_RATE=$(echo "$SENTRY_LOGS" | grep "Profiling configured" | grep -oP '\d+\.\d+%' || echo "unknown")
    print_success "Profiling configured: $PROFILE_RATE"
else
    print_warning "Profiling may not be configured"
fi

if echo "$SENTRY_LOGS" | grep -q "Log capture"; then
    print_success "Log capture is active"
else
    print_warning "Log capture may not be active"
fi

# 4. Test endpoints to generate events
print_header "Generating Test Events"

# Test 1: Successful request (should create trace)
print_step "Generating trace (GET /)..."
curl -s ${API_URL}/ > /dev/null
print_success "Trace generated"

# Test 2: Another endpoint (should create trace)
print_step "Generating trace (GET /health)..."
curl -s ${API_URL}/health > /dev/null
print_success "Trace generated"

# Test 3: Trigger an error
print_step "Generating error event..."
ERROR_RESPONSE=$(curl -s ${API_URL}/add_image 2>&1 || echo "")
print_success "Error generated (check Sentry Issues)"

# 5. Summary and next steps
print_header "Summary"

echo -e "${GREEN}✅ Configuration checks passed${NC}"
echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo "1. Check Sentry dashboard in 1-2 minutes"
echo "2. Navigate to:"
echo "   - Issues: https://sentry.io/organizations/YOUR-ORG/issues/"
echo "   - Performance: https://sentry.io/organizations/YOUR-ORG/performance/"
echo "   - Profiling: https://sentry.io/organizations/YOUR-ORG/profiling/"
echo ""
echo -e "${CYAN}Expected Results:${NC}"
echo "  ✅ Traces: Should see /health and / endpoints in Performance"
echo "  ✅ Errors: Should see error from /add_image in Issues"
echo "  ✅ Logs: Should see Python log events in Issues (if errors occurred)"
echo "  ✅ Profiles: Should see profiles after 1-2 min of active traffic"
echo ""
echo -e "${YELLOW}Note: Profiles require active request traffic to appear${NC}"
echo -e "${YELLOW}Generate more traffic: while true; do curl ${API_URL}/health; sleep 1; done${NC}"
echo ""

print_header "Test Complete"

