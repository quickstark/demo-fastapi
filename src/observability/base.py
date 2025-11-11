"""
Abstract base class for observability providers.

Defines the contract that all observability providers (Datadog, Sentry, etc.) must implement.
This allows switching between providers via environment variables without code changes.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Dict, List, ContextManager
from contextlib import contextmanager


class ObservabilityProvider(ABC):
    """
    Abstract base class for observability and error tracking providers.

    All concrete providers must implement these methods to ensure consistent
    behavior across different observability platforms.
    """

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the observability provider.

        This method should:
        - Set up global instrumentation (e.g., patch_all for Datadog)
        - Configure runtime metrics and profiling
        - Establish connection to the observability backend

        Called once at application startup, before framework initialization.
        """
        pass

    @abstractmethod
    def trace_decorator(self, name: str, **kwargs) -> Callable:
        """
        Return a decorator for tracing function/method execution.

        Args:
            name: Name of the trace span
            **kwargs: Provider-specific configuration (service, resource, etc.)

        Returns:
            Decorator function that can be applied to functions/methods

        Example:
            @provider.trace_decorator("api.handler", service="api-service")
            async def handle_request():
                ...
        """
        pass

    @abstractmethod
    @contextmanager
    def trace_context(self, name: str, **kwargs) -> ContextManager:
        """
        Return a context manager for manual trace span creation.

        Args:
            name: Name of the trace span
            **kwargs: Provider-specific configuration

        Returns:
            Context manager for trace span

        Example:
            with provider.trace_context("database.query") as span:
                result = execute_query()
                span.set_tag("rows", len(result))
        """
        pass

    @abstractmethod
    def record_error(
        self,
        exception: Exception,
        error_type: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an error/exception with metadata.

        Args:
            exception: The exception object to record
            error_type: Classification of the error (e.g., "s3_upload_failure")
            tags: Key-value pairs for filtering/grouping (e.g., {"filename": "image.jpg"})
            context: Additional context data for debugging

        Example:
            try:
                upload_file()
            except Exception as e:
                provider.record_error(
                    e,
                    error_type="upload_failure",
                    tags={"service": "s3", "bucket": "images"}
                )
        """
        pass

    @abstractmethod
    def record_event(
        self,
        title: str,
        text: str,
        alert_type: str = "info",
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        """
        Record a custom event (not an error).

        Args:
            title: Event title/summary
            text: Detailed event description
            alert_type: Severity level (info, warning, error, success)
            tags: List of tags for filtering (e.g., ["deployment", "production"])
            **kwargs: Provider-specific additional fields

        Example:
            provider.record_event(
                title="Deployment Started",
                text="Version 1.2.3 deployment initiated",
                alert_type="info",
                tags=["deployment", "v1.2.3"]
            )
        """
        pass

    @abstractmethod
    def set_user_context(self, user_id: str, **kwargs) -> None:
        """
        Associate user information with traces and errors.

        Args:
            user_id: Unique identifier for the user
            **kwargs: Additional user metadata (email, username, etc.)

        Example:
            provider.set_user_context(
                user_id="12345",
                email="user@example.com",
                role="admin"
            )
        """
        pass

    @abstractmethod
    def add_tags(self, tags: Dict[str, Any]) -> None:
        """
        Add tags to the current trace/span.

        Args:
            tags: Key-value pairs to add as tags

        Example:
            provider.add_tags({
                "http.method": "POST",
                "http.status_code": 200
            })
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the name of the observability provider.

        Returns:
            Provider name (e.g., "datadog", "sentry", "noop")
        """
        pass

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """
        Check if the provider is properly configured and enabled.

        Returns:
            True if provider is active and sending data, False otherwise
        """
        pass
