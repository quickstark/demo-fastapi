"""
Sentry observability provider.

Wraps Sentry SDK to implement the ObservabilityProvider interface.
Provides error tracking, performance monitoring, and profiling via Sentry.
"""

import os
import logging
from typing import Any, Callable, Optional, Dict, List, ContextManager
from contextlib import contextmanager

from .base import ObservabilityProvider

logger = logging.getLogger(__name__)


class SentryProvider(ObservabilityProvider):
    """
    Sentry observability provider using sentry-sdk.

    Implements error tracking and performance monitoring via Sentry.
    Requires SENTRY_DSN to be configured.
    """

    def __init__(self):
        """Initialize the Sentry provider."""
        self._initialized = False
        self._enabled = self._check_configuration()
        logger.info(f"SentryProvider initialized - enabled: {self._enabled}")

    def _check_configuration(self) -> bool:
        """
        Validate that required Sentry configuration is present.

        Returns:
            True if Sentry is properly configured, False otherwise
        """
        # Check for required DSN
        sentry_dsn = os.getenv('SENTRY_DSN', '').strip()
        if not sentry_dsn:
            logger.warning("SENTRY_DSN not configured - Sentry will not be initialized")
            return False

        return True

    def initialize(self) -> None:
        """
        Initialize Sentry SDK with integrations.

        Sets up:
        - Automatic error capture
        - Performance monitoring (traces)
        - FastAPI integration
        - HTTPX integration
        - Profiling (if enabled)
        """
        if self._initialized:
            logger.warning("SentryProvider already initialized")
            return

        if not self._enabled:
            logger.warning("Sentry not properly configured - skipping initialization")
            return

        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.starlette import StarletteIntegration
            from sentry_sdk.integrations.httpx import HttpxIntegration
            from sentry_sdk.integrations.logging import LoggingIntegration

            # Get configuration from environment
            dsn = os.getenv('SENTRY_DSN')
            environment = os.getenv('SENTRY_ENVIRONMENT', os.getenv('DD_ENV', 'development'))
            release = os.getenv('SENTRY_RELEASE', os.getenv('DD_VERSION', '1.0.0'))
            traces_sample_rate = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '1.0'))
            profiles_sample_rate = float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.0'))
            send_default_pii = os.getenv('SENTRY_SEND_DEFAULT_PII', 'false').lower() == 'true'
            debug = os.getenv('SENTRY_DEBUG', 'false').lower() == 'true'
            enable_logs = os.getenv('SENTRY_ENABLE_LOGS', 'true').lower() == 'true'
            log_breadcrumb_level = os.getenv('SENTRY_LOG_BREADCRUMB_LEVEL', 'info')
            log_event_level = os.getenv('SENTRY_LOG_EVENT_LEVEL', 'error')
            profile_lifecycle = os.getenv('SENTRY_PROFILE_LIFECYCLE', 'trace')

            # Initialize Sentry SDK
            logger.info("Initializing Sentry SDK...")

            integrations = [
                FastApiIntegration(transaction_style="endpoint"),
                StarletteIntegration(transaction_style="endpoint"),
                HttpxIntegration(),
            ]

            # Note: Profiling is automatically enabled when profiles_sample_rate > 0
            # No separate ProfilingIntegration needed in sentry-sdk 2.0+

            if enable_logs:
                logging_integration = LoggingIntegration(
                    level=self._resolve_log_level(log_breadcrumb_level, logging.INFO),
                    event_level=self._resolve_log_level(log_event_level, logging.ERROR)
                )
                integrations.append(logging_integration)

            init_kwargs = dict(
                dsn=dsn,
                environment=environment,
                release=release,
                traces_sample_rate=traces_sample_rate,
                profiles_sample_rate=profiles_sample_rate,
                profile_lifecycle=profile_lifecycle,
                send_default_pii=send_default_pii,
                debug=debug,
                integrations=integrations,
                attach_stacktrace=os.getenv('SENTRY_ATTACH_STACKTRACE', 'true').lower() == 'true',
                max_breadcrumbs=50,
                before_send=self._before_send_hook,
            )

            if enable_logs:
                init_kwargs["enable_logs"] = True

            try:
                sentry_sdk.init(**init_kwargs)
            except TypeError as type_error:
                if "enable_logs" in str(type_error):
                    logger.warning("Current sentry-sdk version does not support enable_logs; retrying without it")
                    init_kwargs.pop("enable_logs", None)
                    sentry_sdk.init(**init_kwargs)
                else:
                    raise

            logger.info(f"Sentry initialized - env: {environment}, release: {release}")
            logger.info(f"Sentry traces sample rate: {traces_sample_rate * 100}%")
            if profiles_sample_rate > 0:
                logger.info(f"Sentry profiling enabled: {profiles_sample_rate * 100}%")

            self._initialized = True

        except ImportError as e:
            logger.error(f"Failed to import Sentry SDK: {e}")
            logger.error("Install sentry-sdk: pip install sentry-sdk")
            self._enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
            self._enabled = False

    def _before_send_hook(self, event, hint):
        """
        Process events before sending to Sentry.

        Can be used to filter, modify, or enrich events.
        Return None to drop the event.
        """
        # Add service information to all events
        service = os.getenv('DD_SERVICE', 'fastapi-app')
        if 'tags' not in event:
            event['tags'] = {}
        event['tags']['service'] = service

        return event

    def trace_decorator(self, name: str, **kwargs) -> Callable:
        """
        Return a decorator for tracing function/method execution.

        Args:
            name: Name of the trace span (operation)
            **kwargs: Sentry-specific options (op, description, etc.)

        Returns:
            Decorator that wraps the function with Sentry tracing

        Example:
            @provider.trace_decorator("api.upload", op="http.server")
            async def upload_file():
                ...
        """
        if not self._enabled:
            # Return a no-op decorator if Sentry not enabled
            def noop_decorator(func: Callable) -> Callable:
                return func
            return noop_decorator

        import sentry_sdk

        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **func_kwargs):
                with sentry_sdk.start_span(op=kwargs.get('op', 'function'), description=name):
                    return func(*args, **func_kwargs)
            return wrapper
        return decorator

    @contextmanager
    def trace_context(self, name: str, **kwargs) -> ContextManager:
        """
        Return a context manager for manual trace span creation.

        Args:
            name: Name of the trace span (description)
            **kwargs: Sentry-specific span configuration (op, etc.)

        Yields:
            Sentry span object (or None if disabled)

        Example:
            with provider.trace_context("database.query", op="db") as span:
                result = execute_query()
                if span:
                    span.set_data("rows", len(result))
        """
        if not self._enabled:
            # Return a no-op context manager
            yield None
            return

        import sentry_sdk

        # Use sentry_sdk.start_span() context manager
        with sentry_sdk.start_span(op=kwargs.get('op', 'function'), description=name) as span:
            yield span

    def record_error(
        self,
        exception: Exception,
        error_type: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an error with Sentry.

        Args:
            exception: The exception to record
            error_type: Classification of the error
            tags: Key-value pairs for filtering
            context: Additional context data
        """
        if not self._enabled:
            return

        try:
            import sentry_sdk

            # Set additional context
            if error_type:
                sentry_sdk.set_tag("error_type", error_type)

            # Add tags
            if tags:
                for key, value in tags.items():
                    if isinstance(key, tuple) and len(key) == 2:
                        # Handle tuple format: (key, value)
                        sentry_sdk.set_tag(key[0], str(key[1]))
                    else:
                        sentry_sdk.set_tag(str(key), str(value))

            # Add context
            if context:
                sentry_sdk.set_context("additional_context", context)

            # Add service information
            service = os.getenv('DD_SERVICE', 'fastapi-app')
            env = os.getenv('DD_ENV', 'dev')
            version = os.getenv('DD_VERSION', '1.0')

            sentry_sdk.set_tag("service", service)
            sentry_sdk.set_tag("environment", env)
            sentry_sdk.set_tag("version", version)

            # Capture the exception
            sentry_sdk.capture_exception(exception)

            logger.debug(f"Recorded error in Sentry: {error_type or 'unknown'}")

        except Exception as e:
            logger.error(f"Failed to record error in Sentry: {e}")

    def record_event(
        self,
        title: str,
        text: str,
        alert_type: str = "info",
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        """
        Record a custom event via Sentry breadcrumbs.

        Sentry doesn't have a direct "events API" like Datadog, so we use breadcrumbs
        and messages to achieve similar functionality.

        Args:
            title: Event title (used as message)
            text: Event description (included in data)
            alert_type: Severity (maps to Sentry level)
            tags: List of tags (converted to key-value pairs)
            **kwargs: Additional event data
        """
        if not self._enabled:
            return

        try:
            import sentry_sdk

            # Map alert types to Sentry levels
            level_map = {
                "info": "info",
                "warning": "warning",
                "error": "error",
                "success": "info"
            }
            level = level_map.get(alert_type, "info")

            # Add breadcrumb for the event
            breadcrumb_data = {"text": text}
            if tags:
                breadcrumb_data["tags"] = tags
            breadcrumb_data.update(kwargs)

            sentry_sdk.add_breadcrumb(
                category="application.event",
                message=title,
                level=level,
                data=breadcrumb_data
            )

            # For error-level events, also capture as a message
            if alert_type == "error":
                sentry_sdk.capture_message(
                    f"{title}: {text}",
                    level="error",
                    extras=breadcrumb_data
                )

            logger.debug(f"Recorded event in Sentry: {title}")

        except Exception as e:
            logger.error(f"Failed to record event in Sentry: {e}")

    def set_user_context(self, user_id: str, **kwargs) -> None:
        """
        Associate user information with subsequent errors and traces.

        Args:
            user_id: Unique user identifier
            **kwargs: Additional user metadata (email, username, etc.)
        """
        if not self._enabled:
            return

        try:
            import sentry_sdk

            # Build user data dictionary
            user_data = {"id": user_id}
            user_data.update(kwargs)

            # Set user context in Sentry
            sentry_sdk.set_user(user_data)

            logger.debug(f"Set user context: {user_id}")

        except Exception as e:
            logger.error(f"Failed to set user context: {e}")

    def add_tags(self, tags: Dict[str, Any]) -> None:
        """
        Add tags to subsequent events and traces.

        Args:
            tags: Key-value pairs to add as tags
        """
        if not self._enabled:
            return

        try:
            import sentry_sdk

            for key, value in tags.items():
                sentry_sdk.set_tag(str(key), str(value))

            logger.debug(f"Added {len(tags)} tags")

        except Exception as e:
            logger.error(f"Failed to add tags: {e}")

    @property
    def name(self) -> str:
        """Return provider name."""
        return "sentry"

    @property
    def is_enabled(self) -> bool:
        """Check if Sentry is enabled and initialized."""
        return self._enabled and self._initialized

    @staticmethod
    def _resolve_log_level(value: str, default: int) -> int:
        """Convert string log level to logging module constant."""
        if not value:
            return default
        level_name = value.strip().upper()
        return getattr(logging, level_name, default)
