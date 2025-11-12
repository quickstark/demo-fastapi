# Sentry Structured Logging

This document explains how to use Sentry's structured logging API (`sentry_sdk.logger`) throughout the FastAPI application.

## Overview

Sentry provides a powerful structured logging API that sends logs directly to Sentry's Logs UI, where they can be searched, filtered, and analyzed. This is different from the `LoggingIntegration`, which primarily creates breadcrumbs.

## Benefits of Sentry Structured Logging

1. **Searchable Fields**: Use `{placeholder}` syntax in messages for structured data that becomes searchable
2. **Rich Context**: Attach custom metadata via the `extra` parameter
3. **Log Levels**: Support for trace, debug, info, warning, error, and fatal
4. **Aggregation**: Logs are grouped and can be added as columns in Sentry's Logs view
5. **Correlation**: Logs are automatically associated with the current transaction/trace

## Usage

### Basic Example

```python
from src.observability.sentry_logging import get_sentry_logger

logger = get_sentry_logger()
if logger:
    logger.info(
        "User {username} uploaded {filename}",
        extra={
            "username": "alice",
            "filename": "photo.jpg",
            "file_size": 1024000,
            "operation": "image_upload"
        }
    )
```

### Available Helper Functions

The `src/observability/sentry_logging.py` module provides pre-built logging helpers:

#### Image Operations

```python
from src.observability.sentry_logging import (
    log_image_upload_start,
    log_image_upload_success,
    log_image_upload_error,
    log_image_deletion
)

# Start of upload
log_image_upload_start("photo.jpg", "mongo", "image/jpeg")

# Success
log_image_upload_success("photo.jpg", "mongo", "https://s3.../photo.jpg", 
                        labels_count=5, text_count=2)

# Error
log_image_upload_error("photo.jpg", "mongo", "s3_upload_failure", "Connection timeout")

# Deletion
log_image_deletion("12345", "mongo", "photo.jpg", success=True)
```

#### Database Operations

```python
from src.observability.sentry_logging import log_database_operation

log_database_operation("insert", "postgres", "photo.jpg", True)
log_database_operation("delete", "mongo", "12345", False, "Connection refused")
```

#### Content Analysis

```python
from src.observability.sentry_logging import (
    log_rekognition_analysis,
    log_content_moderation
)

# Rekognition results
log_rekognition_analysis("photo.jpg", 
                        labels=["cat", "pet", "animal"],
                        text=["Hello", "World"],
                        moderation=["Suggestive"])

# Moderation check
log_content_moderation("photo.jpg", labels=["Suggestive"], triggered=True)
```

#### YouTube Processing

```python
from src.observability.sentry_logging import (
    log_youtube_processing_start,
    log_youtube_processing_complete,
    log_youtube_batch_processing
)

# Single video
log_youtube_processing_complete(
    url="https://youtube.com/watch?v=...",
    video_id="abc123",
    title="Great Video",
    duration=45.2,
    save_notion=True
)

# Batch processing
log_youtube_batch_processing(
    urls_count=10,
    strategy="parallel_individual",
    successful=9,
    failed=1,
    total_duration=120.5
)
```

#### S3 Operations

```python
from src.observability.sentry_logging import log_s3_operation

log_s3_operation("upload", "photo.jpg", "my-bucket", True, size_bytes=1024000)
log_s3_operation("delete", "photo.jpg", "my-bucket", False)
```

#### Custom Logging

```python
from src.observability.sentry_logging import log_custom

log_custom(
    "info",
    "Processing batch {batch_id} with {count} items",
    batch_id="batch-001",
    count=50,
    operation="batch_processing",
    user_id="user-123"
)
```

## Log Levels

Use appropriate log levels:

- **`trace`**: Very detailed debugging information (rarely used)
- **`debug`**: Diagnostic information for troubleshooting
- **`info`**: General informational messages about normal operations
- **`warning`**: Unexpected situations that don't prevent operation
- **`error`**: Errors that occurred but were handled
- **`fatal`**: Critical errors that require immediate attention

## Best Practices

### 1. Use Structured Messages

**Good:**
```python
logger.info(
    "Image {filename} uploaded to {backend} in {duration}ms",
    extra={
        "filename": "photo.jpg",
        "backend": "postgres",
        "duration": 123,
        "operation": "image_upload"
    }
)
```

**Bad:**
```python
logger.info(f"Image photo.jpg uploaded to postgres in 123ms")
```

### 2. Add Consistent Tags

Always include an `operation` tag to group related logs:

```python
extra={
    "operation": "image_upload",  # Consistent tag for grouping
    "stage": "complete",          # Where in the process
    "status": "success",          # Outcome
    # ... other fields
}
```

### 3. Include Context

Add relevant business context:

```python
extra={
    "user_id": user.id,
    "request_id": request_id,
    "correlation_id": correlation_id,
    "environment": os.getenv("DD_ENV")
}
```

### 4. Handle Sensitive Data

Never log:
- Passwords
- API keys
- Personal identification numbers
- Credit card data

**Good:**
```python
extra={
    "username": user.username,  # OK
    "user_id": user.id          # OK
}
```

**Bad:**
```python
extra={
    "password": password,        # NEVER
    "api_key": api_key          # NEVER
}
```

## Integration Status

Sentry structured logging is currently integrated in:

- ✅ **Image Upload** (`/add_image`): Start, success, errors, moderation
- ✅ **Image Deletion** (`/delete_image/{id}`): Success and failures
- ✅ **Database Operations**: All backend interactions (Mongo, Postgres, SQL Server)
- ✅ **S3 Operations**: Uploads and deletions
- ✅ **Rekognition Analysis**: Label and text detection
- ✅ **Content Moderation**: Triggered and passed checks
- ✅ **YouTube Processing**: Single and batch video processing
- ✅ **Health Checks** (`/health`): Service status

## Viewing Logs in Sentry

1. Navigate to your Sentry project
2. Go to **Logs** in the left sidebar
3. Use the search bar to filter by:
   - Log message text
   - Structured field names (e.g., `operation:image_upload`)
   - Log levels
   - Time ranges
4. Add frequently used fields as columns for better visibility
5. Create saved searches for common queries

## Example Queries

In Sentry's Logs UI:

- All image uploads: `operation:image_upload`
- Failed operations: `status:failed`
- Specific backend: `backend:postgres`
- Content moderation triggers: `moderation_triggered:true`
- YouTube batch processing: `operation:youtube_batch_processing`
- High processing times: `processing_duration:>5000`

## Configuration

Sentry logging is automatically enabled when:

1. `OBSERVABILITY_PROVIDER=sentry` in your `.env`
2. `SENTRY_DSN` is configured
3. `SENTRY_ENABLE_LOGS=true` (set in Dockerfile by default)

The logging helpers gracefully no-op when Sentry is disabled or when using a different observability provider (e.g., Datadog).

## Performance Considerations

- Structured logging has minimal overhead (~1-2ms per log call)
- Logs are sent asynchronously and don't block request processing
- Consider log volume in high-traffic scenarios
- Use `debug` level sparingly in production

## Further Reading

- [Sentry Logging Documentation](https://docs.sentry.io/platforms/python/usage/logs/)
- [FastAPI Observability Best Practices](../README.md#observability)
- [Datadog vs Sentry Comparison](../README.md#observability-providers)

