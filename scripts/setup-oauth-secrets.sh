#!/bin/bash

# Quick script to set Tailscale OAuth secrets

echo "Setting up Tailscale OAuth secrets for GitHub Actions"
echo ""
echo "You'll need your OAuth client credentials from:"
echo "https://login.tailscale.com/admin/settings/oauth"
echo ""

read -p "Enter your OAuth Client ID (starts with 'k'): " CLIENT_ID
read -sp "Enter your OAuth Client Secret (starts with 'tskey-client-'): " CLIENT_SECRET
echo ""

echo ""
echo "Setting secrets in GitHub..."

gh secret set TAILSCALE_OAUTH_CLIENT_ID --body "$CLIENT_ID"
gh secret set TAILSCALE_OAUTH_CLIENT_SECRET --body "$CLIENT_SECRET"

echo ""
echo "✅ Secrets set successfully!"
echo ""
echo "Verifying secrets are set:"
gh secret list | grep TAILSCALE || echo "No Tailscale secrets found"
