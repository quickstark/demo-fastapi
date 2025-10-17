#!/bin/bash

# Setup Datadog monitoring for SonarQube
# This script configures the conf.d checks for reliable monitoring

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== SonarQube Datadog Monitoring Setup ===${NC}"

# Configuration
DATADOG_CONF_DIR="./datadog-conf.d"
SONARQUBE_HOST="${SONARQUBE_HOST:-sonarqube}"
SONARQUBE_PORT="${SONARQUBE_PORT:-9000}"

# Create directory structure
echo -e "${BLUE}Creating configuration directories...${NC}"
mkdir -p "$DATADOG_CONF_DIR/sonarqube.d"
mkdir -p "$DATADOG_CONF_DIR/http_check.d"
mkdir -p "$DATADOG_CONF_DIR/process.d"

# Choose monitoring method
echo -e "${YELLOW}Select monitoring method(s):${NC}"
echo "1) HTTP checks only (simplest)"
echo "2) Process monitoring (recommended)"
echo "3) JMX monitoring (requires JMX setup)"
echo "4) All methods"
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo -e "${BLUE}Setting up HTTP monitoring...${NC}"
        cp datadog-conf.d/sonarqube.d/http_check.yaml "$DATADOG_CONF_DIR/http_check.d/sonarqube.yaml"
        echo -e "${GREEN}✅ HTTP monitoring configured${NC}"
        ;;
    2)
        echo -e "${BLUE}Setting up Process monitoring...${NC}"
        cp datadog-conf.d/sonarqube.d/process_check.yaml "$DATADOG_CONF_DIR/process.d/sonarqube.yaml"
        echo -e "${GREEN}✅ Process monitoring configured${NC}"
        ;;
    3)
        echo -e "${BLUE}Setting up JMX monitoring...${NC}"
        cp datadog-conf.d/sonarqube.d/conf.yaml "$DATADOG_CONF_DIR/sonarqube.d/conf.yaml"
        echo -e "${YELLOW}⚠️  Remember to enable JMX in your SonarQube container!${NC}"
        echo "Add these environment variables to SonarQube:"
        echo '  SONAR_WEB_JAVAADDITIONALOPTS=-Dcom.sun.management.jmxremote=true -Dcom.sun.management.jmxremote.port=10443 ...'
        echo -e "${GREEN}✅ JMX monitoring configured${NC}"
        ;;
    4)
        echo -e "${BLUE}Setting up all monitoring methods...${NC}"
        cp datadog-conf.d/sonarqube.d/http_check.yaml "$DATADOG_CONF_DIR/http_check.d/sonarqube.yaml"
        cp datadog-conf.d/sonarqube.d/process_check.yaml "$DATADOG_CONF_DIR/process.d/sonarqube.yaml"
        cp datadog-conf.d/sonarqube.d/conf.yaml "$DATADOG_CONF_DIR/sonarqube.d/conf.yaml"
        echo -e "${GREEN}✅ All monitoring methods configured${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Update SonarQube host if needed
if [ "$SONARQUBE_HOST" != "sonarqube" ]; then
    echo -e "${BLUE}Updating SonarQube host to: $SONARQUBE_HOST${NC}"
    find "$DATADOG_CONF_DIR" -name "*.yaml" -exec sed -i "s/sonarqube:9000/$SONARQUBE_HOST:$SONARQUBE_PORT/g" {} \;
    find "$DATADOG_CONF_DIR" -name "*.yaml" -exec sed -i "s/host: sonarqube/host: $SONARQUBE_HOST/g" {} \;
fi

# Check if Datadog agent is running
echo -e "${BLUE}Checking Datadog agent...${NC}"
if docker ps | grep -q datadog-agent; then
    echo -e "${BLUE}Restarting Datadog agent to apply configuration...${NC}"
    docker restart datadog-agent
    
    echo -e "${BLUE}Waiting for agent to start...${NC}"
    sleep 10
    
    echo -e "${BLUE}Checking agent status...${NC}"
    docker exec datadog-agent agent status | grep -A 5 "Checks" || true
    
    echo -e "${GREEN}✅ Datadog agent restarted with new configuration${NC}"
else
    echo -e "${YELLOW}⚠️  Datadog agent container not found${NC}"
    echo "Start your Datadog agent with volume mount:"
    echo "  docker run -v $DATADOG_CONF_DIR:/conf.d:ro ... datadog/agent:latest"
fi

echo
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo
echo "Next steps:"
echo "1. Ensure SonarQube is running at $SONARQUBE_HOST:$SONARQUBE_PORT"
echo "2. Wait 2-3 minutes for metrics to appear in Datadog"
echo "3. Check metrics at: https://app.datadoghq.com/metric/explorer"
echo "4. Search for:"
echo "   - network.http.* (HTTP checks)"
echo "   - process.up (Process checks)"
echo "   - jvm.* (JMX metrics if configured)"
echo
echo "To debug issues:"
echo "  docker exec datadog-agent agent status"
echo "  docker exec datadog-agent agent check sonarqube"
echo "  docker logs datadog-agent | grep sonarqube"
