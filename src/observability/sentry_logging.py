"""
Sentry structured logging utility.

Provides helpers for using sentry_sdk.logger APIs throughout the application.
These logs appear in Sentry's Logs UI and can be searched/filtered.
"""

import os
from typing import Dict, Any, Optional


def get_sentry_logger():
    """
    Get the Sentry logger if Sentry is enabled, otherwise return None.
    
    Returns:
        sentry_sdk.logger or None
    """
    try:
        from src.observability import get_provider
        provider = get_provider()
        
        if provider.name == "sentry" and provider.is_enabled:
            import sentry_sdk
            return sentry_sdk.logger
    except Exception:
        pass
    
    return None


def log_image_upload_start(filename: str, backend: str, content_type: str) -> None:
    """Log the start of an image upload operation."""
    logger = get_sentry_logger()
    if logger:
        logger.info(
            "Image upload started: {filename} to {backend}",
            extra={
                "filename": filename,
                "backend": backend,
                "content_type": content_type,
                "operation": "image_upload",
                "stage": "start"
            }
        )


def log_image_upload_success(filename: str, backend: str, s3_url: str, 
                             labels_count: int, text_count: int) -> None:
    """Log successful image upload."""
    logger = get_sentry_logger()
    if logger:
        logger.info(
            "Image upload successful: {filename} uploaded to {backend}",
            extra={
                "filename": filename,
                "backend": backend,
                "s3_url": s3_url,
                "labels_detected": labels_count,
                "text_detected": text_count,
                "operation": "image_upload",
                "stage": "complete",
                "status": "success"
            }
        )


def log_image_upload_error(filename: str, backend: str, error_type: str, 
                          error_message: str) -> None:
    """Log failed image upload."""
    logger = get_sentry_logger()
    if logger:
        logger.error(
            "Image upload failed: {filename} to {backend} - {error_type}",
            extra={
                "filename": filename,
                "backend": backend,
                "error_type": error_type,
                "error_message": error_message,
                "operation": "image_upload",
                "stage": "failed",
                "status": "error"
            }
        )


def log_image_deletion(image_id: str, backend: str, filename: str, success: bool) -> None:
    """Log image deletion operation."""
    logger = get_sentry_logger()
    if logger:
        level = logger.info if success else logger.error
        level(
            "Image deletion {status}: {filename} from {backend}",
            extra={
                "image_id": image_id,
                "backend": backend,
                "filename": filename,
                "operation": "image_delete",
                "status": "success" if success else "failed"
            }
        )


def log_content_moderation(filename: str, labels: list, triggered: bool) -> None:
    """Log content moderation check results."""
    logger = get_sentry_logger()
    if logger:
        level = logger.warning if triggered else logger.debug
        level(
            "Content moderation check: {filename} - {result}",
            extra={
                "filename": filename,
                "moderation_labels": ", ".join(labels) if labels else "none",
                "moderation_triggered": triggered,
                "label_count": len(labels),
                "operation": "content_moderation",
                "check_type": "image_analysis"
            }
        )


def log_rekognition_analysis(filename: str, labels: list, text: list, 
                            moderation: list) -> None:
    """Log Amazon Rekognition analysis results."""
    logger = get_sentry_logger()
    if logger:
        logger.info(
            "Rekognition analysis complete for {filename}",
            extra={
                "filename": filename,
                "labels_count": len(labels),
                "text_count": len(text),
                "moderation_count": len(moderation),
                "labels": ", ".join(labels[:5]),  # First 5 labels
                "text_detected": ", ".join(text[:3]),  # First 3 text items
                "operation": "rekognition_analysis",
                "service": "aws_rekognition"
            }
        )


def log_database_operation(operation: str, backend: str, record_id: str, 
                          success: bool, error: Optional[str] = None) -> None:
    """Log database operations."""
    logger = get_sentry_logger()
    if logger:
        level = logger.info if success else logger.error
        level(
            "Database {operation}: {backend} - {status}",
            extra={
                "operation": operation,
                "backend": backend,
                "record_id": record_id,
                "status": "success" if success else "failed",
                "error": error,
                "database_type": backend
            }
        )


def log_youtube_processing_start(url: str, video_id: Optional[str] = None) -> None:
    """Log start of YouTube video processing."""
    logger = get_sentry_logger()
    if logger:
        logger.info(
            "YouTube processing started for video {video_id}",
            extra={
                "url": url,
                "video_id": video_id or "unknown",
                "operation": "youtube_processing",
                "stage": "start"
            }
        )


def log_youtube_processing_complete(url: str, video_id: str, title: str, 
                                   duration: float, save_notion: bool) -> None:
    """Log successful YouTube video processing."""
    logger = get_sentry_logger()
    if logger:
        logger.info(
            "YouTube processing complete: {title} ({video_id})",
            extra={
                "url": url,
                "video_id": video_id,
                "title": title,
                "processing_duration": duration,
                "saved_to_notion": save_notion,
                "operation": "youtube_processing",
                "stage": "complete",
                "status": "success"
            }
        )


def log_youtube_batch_processing(urls_count: int, strategy: str, 
                                successful: int, failed: int, 
                                total_duration: float) -> None:
    """Log YouTube batch processing results."""
    logger = get_sentry_logger()
    if logger:
        logger.info(
            "YouTube batch processing: {successful}/{total} videos",
            extra={
                "total_videos": urls_count,
                "successful": successful,
                "failed": failed,
                "strategy": strategy,
                "total_duration": total_duration,
                "success_rate": f"{(successful/urls_count*100):.1f}%",
                "operation": "youtube_batch_processing",
                "stage": "complete"
            }
        )


def log_s3_operation(operation: str, key: str, bucket: str, success: bool, 
                    size_bytes: Optional[int] = None) -> None:
    """Log S3 operations."""
    logger = get_sentry_logger()
    if logger:
        level = logger.info if success else logger.error
        level(
            "S3 {operation}: {key} - {status}",
            extra={
                "operation": operation,
                "s3_key": key,
                "s3_bucket": bucket,
                "status": "success" if success else "failed",
                "size_bytes": size_bytes,
                "service": "aws_s3"
            }
        )


def log_api_request(endpoint: str, method: str, status_code: int, 
                   response_time: float, user_agent: Optional[str] = None) -> None:
    """Log API request."""
    logger = get_sentry_logger()
    if logger:
        level = logger.info if status_code < 400 else logger.warning
        level(
            "API request: {method} {endpoint} - {status_code}",
            extra={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time_ms": response_time * 1000,
                "user_agent": user_agent,
                "operation": "api_request"
            }
        )


def log_health_check(status: str, provider: str, provider_enabled: bool) -> None:
    """Log health check."""
    logger = get_sentry_logger()
    if logger:
        logger.debug(
            "Health check: {status} - observability provider: {provider}",
            extra={
                "status": status,
                "observability_provider": provider,
                "observability_enabled": provider_enabled,
                "operation": "health_check"
            }
        )


def log_custom(level: str, message: str, **extra_fields) -> None:
    """
    Log a custom structured message.
    
    Args:
        level: Log level (trace, debug, info, warning, error, fatal)
        message: Message template with {placeholders}
        **extra_fields: Additional structured data
    """
    logger = get_sentry_logger()
    if logger:
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message, extra=extra_fields)

