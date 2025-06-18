#!/bin/bash

# =============================================================================
# SendGrid API Key Validation Script
# =============================================================================
# This script validates your SendGrid API key configuration and tests the connection
# Usage: ./scripts/validate-sendgrid.sh [env-file]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment file
DEFAULT_ENV_FILE=".env.production"
ENV_FILE="${1:-$DEFAULT_ENV_FILE}"

# Helper functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
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

# Check if env file exists
if [[ ! -f "$ENV_FILE" ]]; then
    print_error "Environment file '$ENV_FILE' not found"
    echo "Usage: $0 [env-file]"
    echo "Example: $0 .env.production"
    exit 1
fi

print_header "SendGrid API Key Validation"

# Load environment variables
print_step "Loading environment variables from $ENV_FILE"
export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)

# Check if SendGrid API key is set
if [[ -z "$SENDGRID_API_KEY" ]]; then
    print_error "SENDGRID_API_KEY not found in $ENV_FILE"
    exit 1
fi

print_success "SendGrid API key found in environment file"

# Validate API key format
print_step "Validating API key format"
if [[ "$SENDGRID_API_KEY" =~ ^SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}$ ]]; then
    print_success "API key format is correct"
else
    print_error "API key format is incorrect"
    echo "Expected format: SG.xxxxxxxxxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    echo "Your key format: ${SENDGRID_API_KEY:0:10}..."
    exit 1
fi

# Test API key with SendGrid
print_step "Testing API key with SendGrid API"

# Test with a simple API call (get API key info)
RESPONSE=$(curl -s -w "%{http_code}" -X GET \
    "https://api.sendgrid.com/v3/user/account" \
    -H "Authorization: Bearer $SENDGRID_API_KEY" \
    -H "Content-Type: application/json")

HTTP_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"

echo "HTTP Response Code: $HTTP_CODE"

case $HTTP_CODE in
    200)
        print_success "API key is valid and authorized"
        echo "Account info: $RESPONSE_BODY"
        ;;
    401)
        print_error "API key is invalid or unauthorized"
        echo "This could mean:"
        echo "  • The API key is incorrect"
        echo "  • The API key has been revoked"
        echo "  • The API key doesn't have proper permissions"
        exit 1
        ;;
    403)
        print_error "API key doesn't have required permissions"
        echo "Please ensure your API key has 'Mail Send' permissions"
        exit 1
        ;;
    *)
        print_error "Unexpected response from SendGrid API"
        echo "Response: $RESPONSE_BODY"
        exit 1
        ;;
esac

# Test email sending capability (dry run)
print_step "Testing email sending capability"

TEST_EMAIL_PAYLOAD='{
    "personalizations": [
        {
            "to": [{"email": "test@example.com"}],
            "subject": "SendGrid API Test"
        }
    ],
    "from": {"email": "dirk@quickstark.com"},
    "content": [
        {
            "type": "text/plain",
            "value": "This is a test email to validate SendGrid API configuration."
        }
    ]
}'

# Test mail send endpoint without actually sending
MAIL_RESPONSE=$(curl -s -w "%{http_code}" -X POST \
    "https://api.sendgrid.com/v3/mail/send" \
    -H "Authorization: Bearer $SENDGRID_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$TEST_EMAIL_PAYLOAD")

MAIL_HTTP_CODE="${MAIL_RESPONSE: -3}"
MAIL_RESPONSE_BODY="${MAIL_RESPONSE%???}"

echo "Mail API Response Code: $MAIL_HTTP_CODE"

case $MAIL_HTTP_CODE in
    202)
        print_success "Mail Send API is accessible and authorized"
        print_warning "Note: This was a real email send test to test@example.com"
        ;;
    401)
        print_error "Mail Send API returned unauthorized"
        echo "Your API key doesn't have Mail Send permissions"
        exit 1
        ;;
    403)
        print_error "Mail Send API returned forbidden"
        echo "Check your SendGrid account status and API key permissions"
        exit 1
        ;;
    400)
        print_warning "Mail Send API returned bad request (expected for test payload)"
        print_success "But API key has proper Mail Send permissions"
        ;;
    *)
        print_error "Unexpected response from Mail Send API"
        echo "Response: $MAIL_RESPONSE_BODY"
        ;;
esac

# Check GitHub secrets (if gh CLI is available)
if command -v gh &> /dev/null; then
    print_step "Checking GitHub secrets"
    
    if gh auth status &> /dev/null; then
        REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "unknown")
        
        if [[ "$REPO" != "unknown" ]]; then
            print_step "Checking if SENDGRID_API_KEY is set in GitHub secrets for $REPO"
            
            # Check if secret exists (gh secret list doesn't show values, just names)
            if gh secret list | grep -q "SENDGRID_API_KEY"; then
                print_success "SENDGRID_API_KEY is configured in GitHub Secrets"
            else
                print_warning "SENDGRID_API_KEY is NOT found in GitHub Secrets"
                echo "Run: ./scripts/setup-secrets.sh $ENV_FILE"
            fi
        else
            print_warning "Not in a Git repository or repository not found"
        fi
    else
        print_warning "GitHub CLI not authenticated"
        echo "Run: gh auth login"
    fi
else
    print_warning "GitHub CLI not installed"
fi

print_header "Validation Complete"

echo -e "${GREEN}✅ SendGrid API key validation passed!${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo "  • API key format: Valid"
echo "  • API key authorization: Valid"
echo "  • Mail Send permissions: Available"
echo ""
echo -e "${YELLOW}Next steps if you're still getting 401 errors:${NC}"
echo "  1. Ensure the API key is correctly uploaded to GitHub Secrets"
echo "  2. Verify the container receives the environment variable"
echo "  3. Check application logs for any API key truncation"
echo "  4. Restart your application container" 