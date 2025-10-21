#!/bin/bash
# GitHub Actions Runner - Startup Script
# This script installs dependencies before starting the runner

set -e

echo "============================================"
echo "GitHub Actions Runner - Startup Script"
echo "============================================"

# Install Node.js if not present
if ! command -v node &> /dev/null; then
  echo "📦 Installing Node.js 20.x..."
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash - 2>&1 | grep -v "^#" || true
  apt-get install -y nodejs
  echo "✅ Node.js installed: $(node --version)"
else
  echo "✅ Node.js already installed: $(node --version)"
fi

# Install python3-venv if not present
if ! python3 -m venv --help &> /dev/null 2>&1; then
  echo "📦 Installing python3-venv..."
  apt-get update -qq && apt-get install -y python3-venv
  echo "✅ python3-venv installed"
else
  echo "✅ python3-venv already installed"
fi

# Install datadog-ci if not present
if ! command -v datadog-ci &> /dev/null; then
  echo "📦 Installing @datadog/datadog-ci..."
  npm install -g @datadog/datadog-ci
  echo "✅ datadog-ci installed: $(datadog-ci version)"
else
  echo "✅ datadog-ci already installed: $(datadog-ci version)"
fi

echo "============================================"
echo "Packages installed successfully!"
echo "Node.js: $(node --version 2>/dev/null || echo 'not found')"
echo "npm: $(npm --version 2>/dev/null || echo 'not found')"
echo "datadog-ci: $(datadog-ci version 2>/dev/null || echo 'not found')"
echo "============================================"

