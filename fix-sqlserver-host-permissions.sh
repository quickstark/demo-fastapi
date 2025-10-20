#!/bin/bash

# SQL Server Permission Fix for Existing Setup
# This fixes permissions on the host directory for SQL Server container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}SQL Server Host Directory Permission Fix${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# SQL Server mssql user UID and GID
MSSQL_UID=10001
MSSQL_GID=0

# Your SQL Server data directory
SQL_DATA_DIR="/docker/appdata/sqlserver2019"

echo -e "${YELLOW}This script will fix permissions for: ${SQL_DATA_DIR}${NC}"
echo -e "${YELLOW}This requires sudo access.${NC}"
echo ""

# Check if directory exists
if [ ! -d "$SQL_DATA_DIR" ]; then
    echo -e "${YELLOW}Directory doesn't exist. Creating it...${NC}"
    sudo mkdir -p "$SQL_DATA_DIR"
fi

# Stop the container first if it's running
echo -e "${YELLOW}Stopping SQL Server container if running...${NC}"
docker stop sqlserver2019 2>/dev/null || true

# Fix permissions
echo -e "${YELLOW}Fixing permissions on $SQL_DATA_DIR...${NC}"
echo "Setting ownership to UID:GID ${MSSQL_UID}:${MSSQL_GID} (mssql user in container)"

# Change ownership to mssql user (10001:0)
sudo chown -R ${MSSQL_UID}:${MSSQL_GID} "$SQL_DATA_DIR"

# Set proper permissions
sudo chmod -R 755 "$SQL_DATA_DIR"

echo -e "${GREEN}✅ Permissions fixed!${NC}"
echo ""
echo -e "${YELLOW}Directory permissions:${NC}"
ls -la "$SQL_DATA_DIR" | head -5

echo ""
echo -e "${GREEN}Now you can start your SQL Server container:${NC}"
echo "  docker-compose up -d"
echo ""
echo -e "${BLUE}After starting, wait 2-3 minutes for SQL Server to initialize.${NC}"
echo -e "${BLUE}Then check the logs: docker logs sqlserver2019${NC}"

