#!/bin/bash

# =============================================================================
# Amazon SES Email Configuration Validation Script
# =============================================================================
# This script validates your Amazon SES email configuration and tests the connection
# Usage: ./scripts/validate-ses.sh [env-file]

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

print_header "Amazon SES Email Configuration Validation"

# Load environment variables
print_step "Loading environment variables from $ENV_FILE"
export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)

# Check if AWS credentials are set
if [[ -z "$AMAZON_KEY_ID" ]]; then
    print_error "AMAZON_KEY_ID not found in $ENV_FILE"
    exit 1
fi

if [[ -z "$AMAZON_KEY_SECRET" ]]; then
    print_error "AMAZON_KEY_SECRET not found in $ENV_FILE"
    exit 1
fi

print_success "AWS credentials found in environment file"

# Check SES configuration
SES_REGION=${SES_REGION:-us-east-1}
SES_FROM_EMAIL=${SES_FROM_EMAIL:-dirk@quickstark.com}

print_step "SES Configuration:"
echo "  Region: $SES_REGION"
echo "  From Email: $SES_FROM_EMAIL"

# Test AWS CLI access if available
if command -v aws &> /dev/null; then
    print_step "Testing AWS CLI access to SES"
    
    # Configure temporary AWS credentials
    export AWS_ACCESS_KEY_ID="$AMAZON_KEY_ID"
    export AWS_SECRET_ACCESS_KEY="$AMAZON_KEY_SECRET"
    export AWS_DEFAULT_REGION="$SES_REGION"
    
    # Test SES access
    if aws ses describe-configuration-sets --region "$SES_REGION" >/dev/null 2>&1; then
        print_success "AWS SES API is accessible"
        
        # Check if sender email is verified
        print_step "Checking if sender email is verified"
        if aws ses get-identity-verification-attributes --identities "$SES_FROM_EMAIL" --region "$SES_REGION" --query "VerificationAttributes.\"$SES_FROM_EMAIL\".VerificationStatus" --output text 2>/dev/null | grep -q "Success"; then
            print_success "Sender email $SES_FROM_EMAIL is verified"
        else
            print_warning "Sender email $SES_FROM_EMAIL may not be verified"
            print_warning "Verify it in AWS SES console: https://console.aws.amazon.com/ses/home?region=$SES_REGION#/verified-identities"
        fi
        
        # Check if account is in sandbox mode
        print_step "Checking SES sandbox status"
        if aws ses get-send-quota --region "$SES_REGION" --query "Max24HourSend" --output text 2>/dev/null | grep -q "^200\.0$"; then
            print_warning "SES account appears to be in sandbox mode (24-hour send limit: 200)"
            print_warning "For production, request to move out of sandbox: https://console.aws.amazon.com/ses/home?region=$SES_REGION#/reputation"
        else
            print_success "SES account appears to be out of sandbox mode"
        fi
        
    else
        print_error "Cannot access AWS SES API"
        echo "This could mean:"
        echo "  • AWS credentials are incorrect"
        echo "  • SES is not available in the specified region"
        echo "  • AWS account doesn't have SES permissions"
    fi
else
    print_warning "AWS CLI not installed - skipping direct SES tests"
    echo "Install AWS CLI for more comprehensive testing: https://aws.amazon.com/cli/"
fi

# Test with Python boto3 if available
if command -v python3 &> /dev/null; then
    print_step "Testing SES connectivity with Python boto3"
    
    python3 -c "
import boto3
from botocore.exceptions import ClientError
import sys

try:
    ses_client = boto3.client(
        'ses',
        region_name='$SES_REGION',
        aws_access_key_id='$AMAZON_KEY_ID',
        aws_secret_access_key='$AMAZON_KEY_SECRET'
    )
    
    # Test SES connectivity
    response = ses_client.describe_configuration_sets()
    print('✅ SES connectivity test passed')
    
    # Test send quota
    quota = ses_client.get_send_quota()
    print(f'📊 Daily send quota: {quota[\"Max24HourSend\"]}')
    print(f'📊 Send rate: {quota[\"MaxSendRate\"]} emails/second')
    
except ClientError as e:
    print(f'❌ SES ClientError: {e.response[\"Error\"][\"Code\"]} - {e.response[\"Error\"][\"Message\"]}')
    sys.exit(1)
except Exception as e:
    print(f'❌ SES connectivity test failed: {str(e)}')
    sys.exit(1)
"
else
    print_warning "Python3 not available - skipping boto3 test"
fi

# Check GitHub secrets (if gh CLI is available)
if command -v gh &> /dev/null; then
    print_step "Checking GitHub secrets"
    
    if gh auth status &> /dev/null; then
        REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "unknown")
        
        if [[ "$REPO" != "unknown" ]]; then
            print_step "Checking SES-related secrets in GitHub for $REPO"
            
            # Check required secrets
            MISSING_SECRETS=()
            for secret in "AMAZON_KEY_ID" "AMAZON_KEY_SECRET" "SES_REGION" "SES_FROM_EMAIL"; do
                if ! gh secret list | grep -q "$secret"; then
                    MISSING_SECRETS+=("$secret")
                fi
            done
            
            if [[ ${#MISSING_SECRETS[@]} -eq 0 ]]; then
                print_success "All SES-related secrets are configured in GitHub"
            else
                print_warning "Missing GitHub secrets: ${MISSING_SECRETS[*]}"
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

echo -e "${GREEN}✅ Amazon SES configuration validation completed!${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo "  • AWS credentials: Available"
echo "  • SES region: $SES_REGION"
echo "  • From email: $SES_FROM_EMAIL"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Verify sender email in AWS SES console"
echo "  2. Request production access if still in sandbox mode"
echo "  3. Test email sending in your application"
echo "  4. Monitor SES sending statistics and reputation" 