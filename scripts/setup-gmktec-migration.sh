#!/bin/bash

# GMKTec Migration Setup Script
# This script helps generate SSH keys and prepare for migration

set -e

echo "========================================="
echo "GMKTec Migration Setup Script"
echo "========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SSH_KEY_PATH="$HOME/.ssh/gmktec_github_actions"
GMKTEC_HOST="100.66.93.87"

echo -e "${YELLOW}This script will help you set up SSH keys for GMKTec deployment.${NC}"
echo ""

# Step 1: Generate SSH Key
echo -e "${GREEN}Step 1: Generate SSH Key${NC}"
if [ -f "$SSH_KEY_PATH" ]; then
    echo -e "${YELLOW}SSH key already exists at $SSH_KEY_PATH${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing key."
    else
        rm -f "$SSH_KEY_PATH" "$SSH_KEY_PATH.pub"
        ssh-keygen -t ed25519 -f "$SSH_KEY_PATH" -C "github-actions@gmktec" -N ""
        echo -e "${GREEN}✓ New SSH key generated${NC}"
    fi
else
    ssh-keygen -t ed25519 -f "$SSH_KEY_PATH" -C "github-actions@gmktec" -N ""
    echo -e "${GREEN}✓ SSH key generated${NC}"
fi

# Step 2: Display public key for copying
echo ""
echo -e "${GREEN}Step 2: Copy public key to GMKTec host${NC}"
echo "Add the following public key to ~/.ssh/authorized_keys on GMKTec host ($GMKTEC_HOST):"
echo ""
echo "----------------------------------------"
cat "$SSH_KEY_PATH.pub"
echo "----------------------------------------"
echo ""

# Step 3: Test SSH connection (optional)
echo -e "${GREEN}Step 3: Test SSH Connection${NC}"
read -p "Enter your GMKTec username: " GMKTEC_USER
echo ""
echo "Testing SSH connection to $GMKTEC_USER@$GMKTEC_HOST..."
echo "Note: This requires that you've already added the public key to the GMKTec host."
echo ""
read -p "Have you added the public key to GMKTec? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=5 "$GMKTEC_USER@$GMKTEC_HOST" "echo 'SSH connection successful!'" 2>/dev/null; then
        echo -e "${GREEN}✓ SSH connection successful!${NC}"
    else
        echo -e "${RED}✗ SSH connection failed. Please check:${NC}"
        echo "  1. The public key is added to ~/.ssh/authorized_keys on GMKTec"
        echo "  2. You're connected to Tailscale network"
        echo "  3. The username is correct"
    fi
else
    echo "Skipping SSH test."
fi

# Step 4: Generate GitHub Secrets commands
echo ""
echo -e "${GREEN}Step 4: GitHub Secrets${NC}"
echo "Add these secrets to your GitHub repository:"
echo "(Settings → Secrets and variables → Actions → New repository secret)"
echo ""
echo "----------------------------------------"
echo -e "${YELLOW}GMKTEC_USER:${NC}"
echo "$GMKTEC_USER"
echo ""
echo -e "${YELLOW}GMKTEC_SSH_KEY:${NC}"
echo "Copy the entire content below (including BEGIN and END lines):"
echo ""
cat "$SSH_KEY_PATH"
echo ""
echo -e "${YELLOW}GMKTEC_SSH_PASSPHRASE:${NC}"
echo "(Leave empty if no passphrase was set)"
echo ""
echo "----------------------------------------"

# Step 5: Tailscale setup reminder
echo ""
echo -e "${GREEN}Step 5: Tailscale OAuth Authentication${NC}"
echo "Set up Tailscale OAuth client for GitHub Actions:"
echo ""
echo "1. Go to https://tailscale.com/s/oauth-clients"
echo "2. Create a new OAuth client for GitHub Actions"
echo "3. Grant the 'auth_keys' scope (required for v3)"
echo "4. Add these as GitHub secrets:"
echo -e "   ${YELLOW}TAILSCALE_OAUTH_CLIENT_ID:${NC} Your Client ID"
echo -e "   ${YELLOW}TAILSCALE_OAUTH_CLIENT_SECRET:${NC} Your Client Secret"
echo ""

# Step 6: Database configuration reminder
echo -e "${GREEN}Step 6: Database Configuration${NC}"
echo "Ensure your databases are accessible at:"
echo "  - PostgreSQL: 192.168.1.100:9001"
echo "  - SQL Server: 192.168.1.100:9002"
echo "  - Datadog Agent: 192.168.1.200"
echo ""

# Step 7: Update Database Secrets
echo -e "${GREEN}Step 7: Update Database Secrets${NC}"
echo "Update these secrets in GitHub with new values:"
echo "  - PGHOST: 192.168.1.100"
echo "  - PGPORT: 9001"
echo "  - SQLSERVERHOST: 192.168.1.100"
echo "  - SQLSERVERPORT: 9002"
echo "  - DD_AGENT_HOST: 192.168.1.200 (new)"
echo ""

# Step 8: Cleanup reminder
echo -e "${GREEN}Step 8: After Successful Migration${NC}"
echo "Remember to remove these old secrets from GitHub:"
echo "  - SYNOLOGY_HOST"
echo "  - SYNOLOGY_SSH_PORT"
echo "  - SYNOLOGY_USER"
echo "  - SYNOLOGY_SSH_KEY"
echo "  - SYNOLOGY_SSH_PASSPHRASE"
echo ""

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Setup script completed!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Add the public key to GMKTec host"
echo "2. Add secrets to GitHub repository"
echo "3. Set up Tailscale authentication"
echo "4. Commit and push the updated workflow"
echo "5. Monitor the GitHub Actions deployment"
echo ""
echo "For detailed instructions, see: docs/GMKTEC_MIGRATION.md"
