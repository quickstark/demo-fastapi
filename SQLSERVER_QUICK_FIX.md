# SQL Server Quick Fix Commands

## Run These Commands on Your Server

### 1. Stop the Container
```bash
docker stop sqlserver2019
docker rm sqlserver2019  # Optional: remove if you want to recreate
```

### 2. Fix Directory Permissions
```bash
# The mssql user in the container has UID 10001 and GID 0
sudo chown -R 10001:0 /docker/appdata/sqlserver2019
sudo chmod -R 755 /docker/appdata/sqlserver2019
```

### 3. Update Your docker-compose.yml
**Important Change**: Remove the `user: mssql` line from your docker-compose.yml
- The container handles the user switching internally
- Explicitly setting it can cause permission issues

Your updated compose should look like:
```yaml
version: '3.8'

services:
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: sqlserver2019
    restart: unless-stopped
    ports:
      - "9002:1433"
    environment:
      - ACCEPT_EULA=Y
      - MSSQL_SA_PASSWORD=Pass@word123
      - MSSQL_PID=Express
      - MSSQL_MEMORY_LIMIT_MB=1024
      - MSSQL_AGENT_ENABLED=false
      - MSSQL_ENABLE_HADR=0
      - TZ=America/Chicago
    volumes:
      - /docker/appdata/sqlserver2019:/var/opt/mssql:rw
    # user: mssql  # <-- REMOVE THIS LINE
    mem_limit: 2g
    mem_reservation: 2g
    healthcheck:
      test: ["CMD", "/opt/mssql-tools/bin/sqlcmd", "-S", "localhost", "-U", "sa", "-P", "Pass@word123", "-Q", "SELECT 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 120s
    networks:
      - sqlserver_network

networks:
  sqlserver_network:
    driver: bridge
```

### 4. Start the Container
```bash
docker-compose up -d
```

### 5. Wait and Verify
```bash
# Wait 2-3 minutes for initialization
sleep 120

# Check logs
docker logs sqlserver2019

# Test connection
docker exec sqlserver2019 /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'Pass@word123' \
  -Q "SELECT @@VERSION"

# Create the images database
docker exec sqlserver2019 /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'Pass@word123' \
  -Q "IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'images') CREATE DATABASE images"
```

## Update Your FastAPI .env File
```bash
SQLSERVER_ENABLED=true
SQLSERVERHOST=192.168.1.200  # Your server IP
SQLSERVERPORT=9002
SQLSERVERUSER=sa
SQLSERVERPW=Pass@word123
SQLSERVERDB=images
```

## If Problems Persist

### Option 1: Clear Everything and Start Fresh
```bash
# Stop and remove container
docker stop sqlserver2019
docker rm sqlserver2019

# Backup and remove old data (optional)
sudo mv /docker/appdata/sqlserver2019 /docker/appdata/sqlserver2019.backup
sudo mkdir -p /docker/appdata/sqlserver2019

# Set correct permissions on new directory
sudo chown -R 10001:0 /docker/appdata/sqlserver2019
sudo chmod -R 755 /docker/appdata/sqlserver2019

# Start fresh
docker-compose up -d
```

### Option 2: Use a Docker Volume Instead
If bind mount continues to have issues, use a named Docker volume:

```yaml
volumes:
  # Instead of: /docker/appdata/sqlserver2019:/var/opt/mssql:rw
  - sqlserver-data:/var/opt/mssql

# Add at bottom of compose file:
volumes:
  sqlserver-data:
    driver: local
```

## Why This Happens
- SQL Server 2019 container runs as user `mssql` (UID 10001, GID 0) internally
- The bind mount directory must be owned by this UID:GID
- Setting `user: mssql` in compose can interfere with the container's internal user switching
- The container needs to start as root to set up permissions, then switches to mssql user
