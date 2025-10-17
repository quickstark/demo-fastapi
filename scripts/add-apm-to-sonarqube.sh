#!/bin/bash

# Add Datadog APM instrumentation to existing SonarQube container
# This uses your EXISTING Datadog Agent - no new agent needed!
# Just downloads a JAR library that SonarQube will use

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== SonarQube APM Setup (Using YOUR Existing Agent) ===${NC}"
echo -e "${GREEN}This will NOT install another Datadog Agent!${NC}"
echo -e "It only adds a Java library to SonarQube that sends traces to your existing agent."
echo

# Configuration
AGENT_PATH="${1:-./dd-java-agent.jar}"
DD_AGENT_HOST="${DD_AGENT_HOST:-172.17.0.1}"  # Default Docker bridge IP
DD_ENV="${DD_ENV:-homelab}"
DD_SERVICE="${DD_SERVICE:-sonarqube}"

# Download agent if it doesn't exist
if [ ! -f "$AGENT_PATH" ]; then
    echo -e "${YELLOW}Downloading Datadog Java Agent...${NC}"
    wget -O "$AGENT_PATH" 'https://dtdg.co/latest-java-tracer'
    echo -e "${GREEN}✅ Agent downloaded to: $AGENT_PATH${NC}"
else
    echo -e "${GREEN}✅ Agent already exists at: $AGENT_PATH${NC}"
fi

# Generate the JVM options
echo
echo -e "${BLUE}Add these environment variables to your SonarQube container:${NC}"
echo
echo -e "${YELLOW}# For Web Server:${NC}"
cat << EOF
SONAR_WEB_JAVAADDITIONALOPTS=-javaagent:/opt/datadog/dd-java-agent.jar -Ddd.service=${DD_SERVICE}-web -Ddd.env=${DD_ENV} -Ddd.trace.enabled=true -Ddd.profiling.enabled=true -Ddd.agent.host=${DD_AGENT_HOST} -Ddd.agent.port=8126 -Ddd.logs.injection=true -Ddd.jdbc.analytics.enabled=true
EOF

echo
echo -e "${YELLOW}# For Compute Engine:${NC}"
cat << EOF
SONAR_CE_JAVAADDITIONALOPTS=-javaagent:/opt/datadog/dd-java-agent.jar -Ddd.service=${DD_SERVICE}-compute -Ddd.env=${DD_ENV} -Ddd.trace.enabled=true -Ddd.profiling.enabled=true -Ddd.agent.host=${DD_AGENT_HOST} -Ddd.agent.port=8126
EOF

echo
echo -e "${YELLOW}# Add this volume mount:${NC}"
echo "volumes:"
echo "  - $AGENT_PATH:/opt/datadog/dd-java-agent.jar:ro"

echo
echo -e "${BLUE}For docker-compose.yml:${NC}"
cat << EOF

  sonarqube:
    environment:
      - SONAR_WEB_JAVAADDITIONALOPTS=-javaagent:/opt/datadog/dd-java-agent.jar -Ddd.service=${DD_SERVICE}-web -Ddd.env=${DD_ENV} -Ddd.trace.enabled=true -Ddd.profiling.enabled=true -Ddd.agent.host=${DD_AGENT_HOST} -Ddd.agent.port=8126
      - SONAR_CE_JAVAADDITIONALOPTS=-javaagent:/opt/datadog/dd-java-agent.jar -Ddd.service=${DD_SERVICE}-compute -Ddd.env=${DD_ENV} -Ddd.trace.enabled=true -Ddd.agent.host=${DD_AGENT_HOST}
    volumes:
      - $AGENT_PATH:/opt/datadog/dd-java-agent.jar:ro
EOF

echo
echo -e "${GREEN}=== Next Steps ===${NC}"
echo "1. Add the environment variables above to your SonarQube container"
echo "2. Mount the JAR file: $AGENT_PATH:/opt/datadog/dd-java-agent.jar:ro"
echo "3. Restart SonarQube: docker-compose restart sonarqube"
echo "4. View traces at: https://app.datadoghq.com/apm/services"
echo
echo -e "${YELLOW}Important:${NC} Using your EXISTING Datadog Agent at $DD_AGENT_HOST:8126"
echo
echo -e "${BLUE}Verify your existing agent has APM enabled:${NC}"
echo "  docker exec YOUR_AGENT_CONTAINER agent status | grep APM"
echo
echo -e "${BLUE}Common host values for existing agent:${NC}"
echo "  - 172.17.0.1 (Docker default bridge)"
echo "  - host.docker.internal (Docker Desktop)"
echo "  - Your server's IP address"
echo "  - datadog-agent (if in same Docker network)"
