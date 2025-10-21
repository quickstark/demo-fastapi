#!/bin/bash
# Datadog CI Installation Script for GitHub Actions Runner
# This script ensures datadog-ci is installed and available

set -e

echo "=========================================="
echo "Datadog CI Installation Script"
echo "=========================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed"
    echo "Please ensure Node.js is installed in your runner image"
    exit 1
fi

echo "✓ Node.js version: $(node --version)"
echo "✓ npm version: $(npm --version)"

# Check if datadog-ci is already installed globally
if command -v datadog-ci &> /dev/null; then
    echo "✓ datadog-ci is already installed: $(datadog-ci version)"
    exit 0
fi

# Install datadog-ci globally
echo "Installing @datadog/datadog-ci globally..."
if npm install -g @datadog/datadog-ci; then
    echo "✓ Successfully installed datadog-ci"
    
    # Verify installation
    if command -v datadog-ci &> /dev/null; then
        echo "✓ Verified: $(datadog-ci version)"
        exit 0
    else
        echo "WARNING: datadog-ci installed but not in PATH"
        echo "PATH: $PATH"
        exit 1
    fi
else
    echo "ERROR: Failed to install datadog-ci"
    exit 1
fi

