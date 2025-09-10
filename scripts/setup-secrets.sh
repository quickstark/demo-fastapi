lines#!/bin/bash

# =============================================================================
# GitHub Secrets Setup Script
# =============================================================================
# This script automatically uploads environment variables to GitHub Secrets
# Usage: ./scripts/setup-secrets.sh .env.production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) is not installed${NC}"
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not authenticated with GitHub CLI${NC}"
    echo "Run: gh auth login"
    exit 1
fi

# Check if env file is provided
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Please provide an environment file${NC}"
    echo "Usage: $0 <env-file>"
    echo "Example: $0 .env.production"
    exit 1
fi

ENV_FILE="$1"

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Environment file '$ENV_FILE' not found${NC}"
    exit 1
fi

echo -e "${GREEN}🚀 Setting up GitHub Secrets from $ENV_FILE${NC}"
echo ""

# Get repository info
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo -e "${YELLOW}📦 Repository: $REPO${NC}"
echo ""

# Show what variables will be skipped
echo -e "${YELLOW}📋 Variables that will be skipped:${NC}"
echo -e "  • Empty or placeholder values (your-*, sk-your-*, secret_your-*)"
echo -e "  • Manually managed secrets: ${SKIP_VARIABLES[*]}"
echo -e "  • Comments and empty lines"
echo ""

# Define variables to skip (these should be managed manually in GitHub)
SKIP_VARIABLES=("SYNOLOGY_SSH_KEY")

# Counter for secrets
SECRET_COUNT=0
SKIPPED_COUNT=0

# Read the env file and set secrets
while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Extract key and value
    if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
        KEY="${BASH_REMATCH[1]}"
        VALUE="${BASH_REMATCH[2]}"
        
        # Remove quotes if present
        VALUE=$(echo "$VALUE" | sed 's/^["'\'']\|["'\'']$//g')
        
        # Check if this key should be skipped
        if [[ " ${SKIP_VARIABLES[@]} " =~ " ${KEY} " ]]; then
            echo -e "${YELLOW}⏭️  Skipping $KEY (manually managed secret)${NC}"
            ((SKIPPED_COUNT++))
            continue
        fi
        
        # Skip if value is empty or placeholder
        if [[ -z "$VALUE" || "$VALUE" =~ ^(your-|sk-your-|secret_your-) ]]; then
            echo -e "${YELLOW}⏭️  Skipping $KEY (empty or placeholder value)${NC}"
            ((SKIPPED_COUNT++))
            continue
        fi
        
        # Set the secret
        echo -e "${GREEN}✅ Setting secret: $KEY${NC}"
        if echo "$VALUE" | gh secret set "$KEY" --repo "$REPO"; then
            ((SECRET_COUNT++))
        else
            echo -e "${RED}❌ Failed to set secret: $KEY${NC}"
        fi
    fi
done < "$ENV_FILE"

echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo -e "${GREEN}✅ Set $SECRET_COUNT secrets${NC}"
echo -e "${YELLOW}⏭️  Skipped $SKIPPED_COUNT placeholder values${NC}"
echo ""
echo -e "${YELLOW}💡 Next steps:${NC}"
echo "1. Verify secrets in GitHub: https://github.com/$REPO/settings/secrets/actions"
echo "2. Manually verify these secrets are set correctly in GitHub:"
echo "   • SYNOLOGY_SSH_KEY (should be your private SSH key)"
echo "3. Push to main branch to trigger deployment"
echo "4. Monitor the GitHub Actions workflow"
echo ""
echo -e "${YELLOW}⚠️  Important Notes:${NC}"
echo "• SYNOLOGY_SSH_KEY is NOT uploaded by this script (to prevent corruption)"
echo "• Amazon SES configuration uses your existing AWS credentials (AMAZON_KEY_ID/AMAZON_KEY_SECRET)"
echo "• Ensure your SES_FROM_EMAIL is verified in AWS SES console"
echo "• For production, move out of SES sandbox mode in AWS console" 