# Database Configuration Guide

This guide explains how to configure and toggle different database backends in your FastAPI application.

## Environment Toggle System

The application supports three database backends:
- **PostgreSQL** - Always enabled if configured
- **MongoDB** - Always enabled if configured  
- **SQL Server** - Can be toggled on/off via environment variable

## SQL Server Toggle

### Enabling SQL Server

Add to your `.env` file:
```bash
SQLSERVER_ENABLED=true
SQLSERVERHOST=192.168.1.200
SQLSERVERPORT=9002
SQLSERVERUSER=sa
SQLSERVERPW=Pass@word123
SQLSERVERDB=images
```

### Disabling SQL Server

Add to your `.env` file:
```bash
SQLSERVER_ENABLED=false
```

When disabled:
- ✅ Application starts immediately without waiting for SQL Server
- ✅ No connection attempts are made
- ✅ SQL Server endpoints return appropriate "disabled" messages
- ✅ Other backends (PostgreSQL, MongoDB) continue to work normally

## Configuration Examples

### Development - SQL Server Disabled
```bash
# .env.development
SQLSERVER_ENABLED=false

# Use PostgreSQL for development
PGHOST=localhost
PGPORT=5432
PGDATABASE=images_dev
PGUSER=dev_user
PGPASSWORD=dev_pass
```

### Production - All Databases Enabled
```bash
# .env.production
# SQL Server
SQLSERVER_ENABLED=true
SQLSERVERHOST=192.168.1.200
SQLSERVERPORT=9002
SQLSERVERUSER=sa
SQLSERVERPW=YourStrongPassword
SQLSERVERDB=images

# PostgreSQL
PGHOST=192.168.1.200
PGPORT=9001
PGDATABASE=images
PGUSER=postgres
PGPASSWORD=YourPostgresPassword

# MongoDB
MONGO_CONN=mongodb://192.168.1.200:27017
MONGO_USER=mongo_user
MONGO_PW=YourMongoPassword
```

### Testing - Only PostgreSQL
```bash
# .env.testing
SQLSERVER_ENABLED=false

# PostgreSQL only
PGHOST=localhost
PGPORT=5432
PGDATABASE=images_test
PGUSER=test_user
PGPASSWORD=test_pass

# MongoDB disabled by not setting MONGO_CONN
```

## Checking Database Status

### Health Check Endpoint
```bash
# Check application health
curl http://localhost:8000/health

# Returns:
{
  "status": "healthy",
  "service": "fastapi-app",
  "version": "1.0",
  "environment": "dev"
}
```

### Database Status Endpoint
```bash
# Check all database backends
curl http://localhost:8000/api/v1/database-status

# Returns detailed status for each database:
{
  "databases": {
    "sqlserver": {
      "name": "SQL Server",
      "enabled": true,
      "available": true,
      "configured": true,
      "connection": "connected",
      "details": {
        "host": "192.168.1.200",
        "port": 9002,
        "database": "images",
        "message": "Successfully connected to SQL Server"
      }
    },
    "postgres": { ... },
    "mongodb": { ... }
  },
  "summary": {
    "total": 3,
    "enabled": 3,
    "configured": 3,
    "available": 3
  }
}
```

### Database Configuration Endpoint
```bash
# View current configuration (without passwords)
curl http://localhost:8000/api/v1/database-config

# Returns:
{
  "sqlserver": {
    "enabled": true,
    "host": "192.168.1.200",
    "port": 9002,
    "database": "images",
    "user": "***configured***"
  },
  "postgres": { ... },
  "mongodb": { ... }
}
```

### SQL Server Test Endpoint
```bash
# Detailed SQL Server connection test
curl http://localhost:8000/test-sqlserver

# Returns:
{
  "test_type": "sqlserver_debug",
  "timestamp": "2025-01-11T00:00:00Z",
  "results": {
    "connection": true,
    "table_exists": true,
    "simple_insert": true,
    "parameter_test": true,
    "errors": []
  }
}
```

## Using Different Backends

### Via Query Parameter
```bash
# Get all images from PostgreSQL
curl "http://localhost:8000/images?backend=postgres"

# Get all images from MongoDB
curl "http://localhost:8000/images?backend=mongo"

# Get all images from SQL Server
curl "http://localhost:8000/images?backend=sqlserver"
```

### Upload to Specific Backend
```bash
# Upload to PostgreSQL
curl -X POST "http://localhost:8000/add_image?backend=postgres" \
  -F "file=@image.jpg"

# Upload to MongoDB
curl -X POST "http://localhost:8000/add_image?backend=mongo" \
  -F "file=@image.jpg"

# Upload to SQL Server
curl -X POST "http://localhost:8000/add_image?backend=sqlserver" \
  -F "file=@image.jpg"
```

## Error Handling

### When SQL Server is Disabled
```bash
curl "http://localhost:8000/images?backend=sqlserver"

# Returns:
{
  "error": "SQL Server is disabled via SQLSERVER_ENABLED=false",
  "type": "backend_disabled"
}
```

### When SQL Server is Not Configured
```bash
# If SQLSERVERHOST is not set
curl "http://localhost:8000/images?backend=sqlserver"

# Returns:
{
  "error": "SQL Server configuration not found",
  "type": "backend_not_configured"
}
```

### When SQL Server is Unavailable
```bash
# If SQL Server is not reachable
curl "http://localhost:8000/images?backend=sqlserver"

# Returns:
{
  "error": "Failed to get SQL Server connection",
  "type": "connection_error",
  "details": "Connection refused"
}
```

## Runtime Behavior

### Lazy Initialization
- SQL Server connections are established **on first use**, not at startup
- This prevents blocking application startup if SQL Server is unavailable
- Reduces connection timeouts from 30s to 5s for faster failure detection

### Graceful Degradation
- If SQL Server is disabled/unavailable, other backends continue to work
- Each backend operates independently
- No single point of failure

### Logging
```
# When SQL Server is disabled
INFO - SQL Server is disabled via SQLSERVER_ENABLED=false

# When SQL Server is enabled but not configured
WARNING - SQL Server configuration not found. Skipping SQL Server connection.

# When SQL Server connection succeeds
INFO - Successfully connected to SQL Server database: images at 192.168.1.200:9002

# When SQL Server connection fails
ERROR - Error connecting to SQL Server: [Errno 111] Connection refused
```

## Docker Compose Integration

### With SQL Server
```yaml
services:
  fastapi-app:
    environment:
      - SQLSERVER_ENABLED=true
      - SQLSERVERHOST=sqlserver2019
      - SQLSERVERPORT=1433
      # ... other SQL Server vars
    depends_on:
      - sqlserver2019

  sqlserver2019:
    # SQL Server container config
```

### Without SQL Server
```yaml
services:
  fastapi-app:
    environment:
      - SQLSERVER_ENABLED=false
    # No depends_on for sqlserver
```

## Best Practices

### Development
1. Disable SQL Server if not needed: `SQLSERVER_ENABLED=false`
2. Use PostgreSQL for primary development
3. Test with SQL Server periodically before production

### Testing
1. Use separate test databases
2. Consider using SQLite for unit tests
3. Use `SQLSERVER_ENABLED=false` for faster test startup

### Production
1. Enable only the databases you need
2. Monitor all database connections via `/api/v1/database-status`
3. Set up proper health checks in your deployment
4. Use strong passwords and secure connections

### Troubleshooting
1. Check `/api/v1/database-status` first
2. Review `/api/v1/database-config` for configuration issues
3. Use `/test-sqlserver` for detailed SQL Server diagnostics
4. Check application logs for connection errors
5. Verify environment variables are loaded correctly

## Migration Strategy

### Enabling SQL Server in Existing Deployment

1. **Prepare SQL Server**
   ```bash
   # Fix permissions
   sudo chown -R 10001:0 /docker/appdata/sqlserver2019
   
   # Start SQL Server
   docker-compose up -d sqlserver2019
   
   # Wait for initialization
   sleep 120
   ```

2. **Update Environment**
   ```bash
   # Add to .env
   SQLSERVER_ENABLED=true
   SQLSERVERHOST=192.168.1.200
   SQLSERVERPORT=9002
   SQLSERVERUSER=sa
   SQLSERVERPW=Pass@word123
   SQLSERVERDB=images
   ```

3. **Test Connection**
   ```bash
   curl http://localhost:8000/api/v1/database-status
   curl http://localhost:8000/test-sqlserver
   ```

4. **Enable in Production**
   ```bash
   # Update production environment
   # Restart application
   docker-compose restart fastapi-app
   
   # Verify
   curl https://your-domain.com/api/v1/database-status
   ```

### Disabling SQL Server

1. **Update Environment**
   ```bash
   # Set in .env
   SQLSERVER_ENABLED=false
   ```

2. **Restart Application**
   ```bash
   docker-compose restart fastapi-app
   ```

3. **Verify**
   ```bash
   curl http://localhost:8000/api/v1/database-status
   # Should show sqlserver as disabled
   ```

## Environment Variables Reference

### SQL Server
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SQLSERVER_ENABLED` | No | `true` | Enable/disable SQL Server |
| `SQLSERVERHOST` | Yes* | - | SQL Server hostname or IP |
| `SQLSERVERPORT` | No | `1433` | SQL Server port |
| `SQLSERVERUSER` | Yes* | - | SQL Server username |
| `SQLSERVERPW` | Yes* | - | SQL Server password |
| `SQLSERVERDB` | Yes* | - | SQL Server database name |

*Required only if `SQLSERVER_ENABLED=true`

### PostgreSQL
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PGHOST` | Yes | - | PostgreSQL hostname |
| `PGPORT` | No | `5432` | PostgreSQL port |
| `PGDATABASE` | Yes | - | PostgreSQL database |
| `PGUSER` | Yes | - | PostgreSQL username |
| `PGPASSWORD` | Yes | - | PostgreSQL password |

### MongoDB
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MONGO_CONN` | Yes | - | MongoDB connection string |
| `MONGO_USER` | Yes | - | MongoDB username |
| `MONGO_PW` | Yes | - | MongoDB password |

## Summary

The environment toggle system provides:
- ✅ **Flexibility** - Enable/disable databases as needed
- ✅ **Fast Startup** - No blocking on unavailable databases
- ✅ **Graceful Degradation** - Independent backend operation
- ✅ **Easy Debugging** - Status and config endpoints
- ✅ **Production Ready** - Proper error handling and logging
