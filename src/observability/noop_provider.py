"""
No-op observability provider for disabled/testing scenarios.

This provider implements the ObservabilityProvider interface but performs no actions.
Useful for development environments or when observability needs to be disabled.
"""

import logging
from typing import Any, Callable, Optional, Dict, List, ContextManager
from contextlib import contextmanager

from .base import ObservabilityProvider

logger = logging.getLogger(__name__)


class NoopProvider(ObservabilityProvider):
    """
    No-operation observability provider.

    All methods are no-ops (do nothing). Safe to use when observability is disabled
    or during testing. No external dependencies or network calls.
    """

    def __init__(self):
        """Initialize the no-op provider."""
        logger.info("NoopProvider initialized - observability disabled")

    def initialize(self) -> None:
        """No-op initialization."""
        pass

    def trace_decorator(self, name: str, **kwargs) -> Callable:
        """
        Return a no-op decorator.

        Args:
            name: Name of the trace span (ignored)
            **kwargs: Configuration (ignored)

        Returns:
            Pass-through decorator that doesn't modify the function
        """
        def decorator(func: Callable) -> Callable:
            # Return the function unmodified
            return func
        return decorator

    @contextmanager
    def trace_context(self, name: str, **kwargs) -> ContextManager:
        """
        Return a no-op context manager.

        Args:
            name: Name of the trace span (ignored)
            **kwargs: Configuration (ignored)

        Yields:
            None
        """
        # Context manager that does nothing
        yield None

    def record_error(
        self,
        exception: Exception,
        error_type: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        No-op error recording.

        Args:
            exception: The exception (ignored)
            error_type: Error classification (ignored)
            tags: Tags (ignored)
            context: Context data (ignored)
        """
        pass

    def record_event(
        self,
        title: str,
        text: str,
        alert_type: str = "info",
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        """
        No-op event recording.

        Args:
            title: Event title (ignored)
            text: Event description (ignored)
            alert_type: Severity (ignored)
            tags: Tags (ignored)
            **kwargs: Additional fields (ignored)
        """
        pass

    def set_user_context(self, user_id: str, **kwargs) -> None:
        """
        No-op user context.

        Args:
            user_id: User identifier (ignored)
            **kwargs: User metadata (ignored)
        """
        pass

    def add_tags(self, tags: Dict[str, Any]) -> None:
        """
        No-op tag addition.

        Args:
            tags: Tags to add (ignored)
        """
        pass

    @property
    def name(self) -> str:
        """Return provider name."""
        return "noop"

    @property
    def is_enabled(self) -> bool:
        """Noop provider is never 'enabled' in the functional sense."""
        return False
