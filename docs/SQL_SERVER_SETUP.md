# SQL Server Integration Setup and Troubleshooting

## Overview

This document explains the SQL Server integration for the FastAPI Images API, including setup, troubleshooting, and common issues.

## Database Schema

The SQL Server implementation uses a table structure that matches PostgreSQL for compatibility:

```sql
CREATE TABLE images (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    width INT NULL,
    height INT NULL,
    url NVARCHAR(500) NULL,
    url_resize NVARCHAR(500) NULL,
    date_added DATE NULL DEFAULT GETDATE(),
    date_identified DATE NULL,
    ai_labels NVARCHAR(MAX) NULL,  -- JSON data stored as text
    ai_text NVARCHAR(MAX) NULL     -- JSON data stored as text
);
```

## Environment Variables

Required environment variables for SQL Server connectivity:

```bash
SQLSERVERHOST=192.168.1.100
SQLSERVERPORT=9003
SQLSERVERUSER=sqlserver2019
SQLSERVERPW=Vall123@
SQLSERVERDB=images
```

## Dependencies

The implementation uses `python-tds` (pytds) as a pure Python SQL Server driver:

```bash
pip install python-tds>=1.16.0
```

## Automatic Table Creation

The application automatically creates the required table and indexes on first connection:

- Images table with proper schema
- Performance indexes on name, date_added, and date_identified
- Compatible JSON storage using NVARCHAR(MAX) columns

## Common Issues and Solutions

### Issue 1: "not all arguments converted during string formatting"

**Cause**: This error occurs because pytds (python-tds) uses `%s` parameter placeholders, not `?` placeholders like SQLite.

**Solution**: 
- Updated all SQL queries to use `%s` placeholders instead of `?`
- The application now automatically creates the table with proper schema
- Insert query updated to include all required columns with proper defaults

**Technical Details**: 
- **Root Cause**: pytds uses DB-API 2.0 standard with `%s` placeholders
- **Previous**: `VALUES (?, ?, ?, ?, ?, GETDATE(), ?, ?, ?)` - caused formatting error
- **Fixed**: `VALUES (%s, %s, %s, %s, %s, GETDATE(), %s, %s, %s)` - proper pytds syntax
- All SELECT and DELETE queries also updated to use `%s` placeholders

### Issue 2: Missing Environment Variables in Container

**Cause**: SQL Server environment variables not passed to Docker container during deployment.

**Solution**: 
- Added SQL Server environment variables to `.github/workflows/deploy.yaml`
- Added SQL Server environment variables to `docker-compose.yml`
- Updated GitHub Secrets configuration

## Testing SQL Server Integration

### Local Testing

```bash
# Build and run with SQL Server support
./scripts/build.sh --run

# Test SQL Server endpoint
curl "http://localhost:9000/images?backend=sqlserver"
curl -X POST "http://localhost:9000/add_image?backend=sqlserver" -F "file=@test.jpg"
```

### Production Testing

```bash
# Test production API
curl "https://api-images.quickstark.com/images?backend=sqlserver"
curl -X POST "https://api-images.quickstark.com/add_image?backend=sqlserver" -F "file=@test.jpg"
```

## Database Connection Details

- **Driver**: python-tds (Pure Python, no system dependencies)
- **Connection Pooling**: Thread pool executor with max 10 workers
- **Transaction Management**: Auto-commit for SELECT, explicit commit/rollback for INSERT/UPDATE/DELETE
- **Error Handling**: Comprehensive error logging with stack traces
- **Performance**: Indexed queries and connection reuse

## Logging and Monitoring

### Application Logging
SQL Server operations are logged with appropriate levels:

```python
# Connection events
logger.info("Successfully connected to SQL Server database")

# Query operations  
logger.debug("Adding image to SQL Server - AI Labels: {ai_labels}")

# Error conditions
logger.error("Error in add_image_sqlserver: {err}", exc_info=True)
```

### Datadog Database Monitoring & APM

**Issue**: pytds (python-tds) is not automatically instrumented by ddtrace, unlike psycopg for PostgreSQL.

**Solution**: Manual tracing implementation for complete observability:

#### Database Operation Spans (DBM Correlation)
```python
# Each SQL query creates a database span with proper DBM correlation attributes
with tracer.trace("db.query", service="sqlserver", resource=query[:100]) as span:
    span.set_tag("@peer.db.system", "sqlserver")     # Required for DBM correlation
    span.set_tag("@peer.db.name", SQLSERVER_DB)      # Database name for correlation
    span.set_tag("db.statement", query)              # Full SQL statement
    span.set_tag("db.host", SQLSERVER_HOST)          # Database host
    span.set_tag("db.port", SQLSERVER_PORT)          # Database port
    span.set_tag("db.rows_affected", rowcount)       # Query result metadata
```

#### Function-Level Tracing
```python
@tracer.wrap(service="sqlserver", resource="sqlserver.add_image")
async def add_image_sqlserver(name: str, url: str, ai_labels: list, ai_text: list):
    # Function creates a span with descriptive resource naming
    span = tracer.current_span()
    if span:
        span.set_tag("image.name", name)
        span.set_tag("image.labels_count", len(ai_labels))
```

#### Critical DBM Correlation Requirements
- **Operation Name**: Must use `db.query` (not `sqlserver.query`) for DBM recognition
- **Resource Name**: Include query excerpt as resource for query identification  
- **Peer Database Tags**: Use `@peer.db.system` and `@peer.db.name` for correlation
- **Service Consistency**: Use consistent service name across spans and connection Pin

#### What You'll See in Datadog:
- **APM Traces**: Complete request traces showing SQL Server operations within endpoint spans
- **Database Monitoring**: Individual SQL queries with execution times and parameters  
- **Service Map**: SQL Server service connections and dependencies
- **Performance Metrics**: Query performance, connection pooling, error rates

#### Comparison with PostgreSQL:
- **PostgreSQL**: Automatic instrumentation via `patch_all(psycopg=True)`
  - Auto-generates `db.query` spans with correct DBM correlation attributes
  - Uses reserved attributes (`trace_id`, `service`, `resource_name`) automatically
  - Seamless APM-to-DBM correlation out of the box

- **SQL Server**: Manual instrumentation matching auto-instrumentation patterns
  - `@tracer.wrap()` decorators for function-level spans
  - Manual `db.query` spans with `@peer.db.*` correlation tags
  - Explicit resource naming and service consistency
  - Achieves identical DBM correlation through manual implementation

- **Result**: Both provide identical Datadog observability coverage
  - APM traces with nested database spans
  - Database Monitoring with query-to-trace correlation
  - Service map visibility and performance metrics

## Security Considerations

- Environment variables used for credentials (never hardcoded)
- Parameterized queries prevent SQL injection
- Connection timeouts prevent hanging connections
- Proper error handling prevents information leakage

## Performance Optimization

- Connection reuse and pooling
- Indexed queries for fast lookups
- JSON data stored as text for compatibility
- Async operations using thread pool

## Schema Migration

If you need to migrate from an existing schema:

```sql
-- Check existing table structure
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'images';

-- Add missing columns if needed
ALTER TABLE images ADD width INT NULL;
ALTER TABLE images ADD height INT NULL;
-- etc.
```

## Troubleshooting Checklist

### Basic Functionality
1. ✅ Environment variables configured correctly
2. ✅ SQL Server accessible from application host  
3. ✅ Database and user permissions configured
4. ✅ python-tds package installed
5. ✅ Table schema matches expected structure
6. ✅ Network connectivity (ports, firewall)
7. ✅ Container environment variables passed correctly

### Datadog DBM Correlation Issues
If SQL Server queries appear in APM traces but not in Database Monitoring:

8. ✅ Verify span operation name is `db.query` (not `sqlserver.query`)
9. ✅ Check `@peer.db.system` tag is set to `"sqlserver"`
10. ✅ Confirm `@peer.db.name` tag matches actual database name
11. ✅ Ensure service name consistency between spans and Pin.override
12. ✅ Validate resource name includes query excerpt for identification
13. ✅ Check Datadog agent has Database Monitoring enabled
14. ✅ Verify `db.statement` contains full SQL query text

### Debugging DBM Correlation
```bash
# Check APM traces for proper database spans
curl "https://api-images.quickstark.com/add_image?backend=sqlserver" -F "file=@test.jpg"

# In Datadog APM, look for:
# - Service: "sqlserver" 
# - Operation: "db.query"
# - Tags: "@peer.db.system:sqlserver", "@peer.db.name:images"
```

## Contact and Support

For issues with SQL Server integration:
1. Check application logs for detailed error messages
2. Verify environment variables and connectivity
3. Test SQL Server connection independently
4. Review this troubleshooting guide