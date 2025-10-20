# SQL Server Connection Issues - Fixed

## Problem 1: Application Startup Blocked by SQL Server Connection
The FastAPI application was failing to start due to SQL Server connection issues:
- SQL Server at `192.168.1.200:9002` was not accessible (Connection refused)
- The pytds library was retrying with exponential backoff (2.4s, 4.8s, 9.6s...)
- Connection attempts were happening at module load time, blocking application startup

## Problem 2: SQL Server Docker Container Permission Issues
The SQL Server Docker container fails to start with permission errors:
```
Your master database file is owned by UNKNOWN.
sqlservr: Unable to open /var/opt/mssql/.system/instance_id: 
File: pal.cpp:566 [Status: 0xC0000022 Access Denied errno = 0xD(13) Permission denied]
/opt/mssql/bin/sqlservr: PAL initialization failed. Error: 101
```

## Error Log Symptoms
```
ConnectionRefusedError: [Errno 111] Connection refused
pytds - INFO - Will retry after 2.399020 seconds
pytds - INFO - Will retry after 4.798591 seconds
pytds - INFO - Will retry after 9.599191 seconds
```

## Solutions Applied

### 1. Removed Module-Level Connection Initialization
Changed `/src/sqlserver.py` to use lazy initialization instead of connecting at module load time. The connection is now established on first use, not during import.

### 2. Reduced Connection Timeouts
- Changed `timeout` from 30 to 5 seconds
- Changed `login_timeout` from 30 to 5 seconds
- Added socket timeout of 5 seconds for faster failure detection

### 3. Quick Disable Option
You can disable SQL Server entirely by setting in your `.env` file:
```
SQLSERVER_ENABLED=false
```

## Solutions for Docker Permission Issues

### Quick Fix: Use the Provided Script
```bash
# Run the fix script
./scripts/fix-sqlserver-permissions.sh

# Choose option 2 to recreate the container with correct permissions
```

### Manual Fix: Step-by-Step

#### Option 1: Fix Existing Container Permissions
```bash
# Stop the container
docker stop <container-name>

# Fix permissions using a temporary container
docker run --rm \
  --volumes-from <container-name> \
  --user root \
  busybox \
  sh -c "chown -R 10001:0 /var/opt/mssql && chmod -R 755 /var/opt/mssql"

# Start the container again
docker start <container-name>
```

#### Option 2: Use Docker Compose (Recommended)
```bash
# Use the provided docker-compose.sqlserver.yml
docker-compose -f docker-compose.sqlserver.yml up -d

# This will:
# - Create SQL Server with proper permissions
# - Map to port 9002 as expected
# - Create the 'images' database automatically
# - Set up health checks
```

## How to Configure SQL Server

### Option A: Disable SQL Server (if not needed)
1. Edit your `.env` file
2. Set `SQLSERVER_ENABLED=false`
3. Restart the application

### Option B: Configure Correct SQL Server Connection
1. Edit your `.env` file
2. Set the correct SQL Server connection details:
   ```
   SQLSERVER_ENABLED=true
   SQLSERVERHOST=your-actual-host
   SQLSERVERPORT=1433
   SQLSERVERUSER=your-username
   SQLSERVERPW=your-password
   SQLSERVERDB=your-database
   ```
3. Ensure SQL Server is running and accessible
4. Restart the application

### Option C: Use Docker Compose (Recommended for Development)
The project includes `docker-compose.yml` which should set up SQL Server automatically.
```bash
docker-compose up -d
```

## Additional Notes

### LLM Observability Warning
You may also see this warning:
```
Failed to enable LLM Observability: Failed to load dependencies for `ragas_faithfulness` evaluator
```
This is **non-blocking** and the application will continue to run. It's related to optional Datadog LLM monitoring features.

### Testing SQL Server Connection
Once the application is running, you can test SQL Server connectivity at:
```
GET http://localhost:8000/test-sqlserver
```

This endpoint will return detailed information about the SQL Server connection status and any issues.

## Changes Made
1. **File**: `/src/sqlserver.py`
   - Removed module-level `get_connection()` call
   - Added lazy initialization
   - Reduced connection timeouts
   - Improved error handling

These changes ensure the application starts quickly even when SQL Server is unavailable, and SQL Server operations will fail gracefully with appropriate error messages when attempted.
