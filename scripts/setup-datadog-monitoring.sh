#!/bin/bash

# Setup Datadog Monitoring for GitHub Runner
# This script configures Datadog to monitor your GitHub Actions runner

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Datadog Monitoring Setup ===${NC}"

# Check if DD_API_KEY is set
if [ -z "$DD_API_KEY" ]; then
    echo -e "${YELLOW}Warning: DD_API_KEY not set in environment${NC}"
    echo "Please set your Datadog API key:"
    echo "  export DD_API_KEY=your-api-key-here"
    exit 1
fi

# Create monitoring network if it doesn't exist
echo -e "${BLUE}Creating Docker network for monitoring...${NC}"
docker network create monitoring 2>/dev/null || echo "Network already exists"

# Start Datadog agent
echo -e "${BLUE}Starting Datadog agent...${NC}"
docker-compose -f docker-compose.datadog.yml up -d

# Wait for agent to start
sleep 5

# Check agent status
echo -e "${BLUE}Checking Datadog agent status...${NC}"
docker exec datadog-agent agent status

# Configure GitHub runner container labels for monitoring
echo -e "${BLUE}Adding monitoring labels to GitHub runner...${NC}"
docker-compose -f docker-compose.runner.yml down
docker-compose -f docker-compose.runner.yml up -d \
  --scale runner=1 \
  --no-deps

echo -e "${GREEN}✅ Datadog monitoring configured!${NC}"
echo
echo "Monitor your containers at:"
echo "  https://app.datadoghq.com/containers"
echo
echo "View GitHub runner metrics with query:"
echo "  container_name:github-runner"
echo
echo "View FastAPI app metrics with query:"
echo "  container_name:images-api"
