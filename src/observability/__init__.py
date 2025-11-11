"""
Observability provider factory and registry.

Provides a unified interface for switching between observability providers
(Datadog, Sentry, etc.) via environment variables.

Usage:
    from src.observability import get_provider

    # Get the configured provider
    provider = get_provider()

    # Initialize once at application startup
    provider.initialize()

    # Use throughout application
    @provider.trace_decorator("api.handler")
    async def handle_request():
        ...

Environment Variables:
    OBSERVABILITY_PROVIDER: datadog | sentry | disabled (default: datadog)
"""

import os
import logging
from typing import Optional

from .base import ObservabilityProvider
from .noop_provider import NoopProvider
from .datadog_provider import DatadogProvider
from .sentry_provider import SentryProvider

logger = logging.getLogger(__name__)

# Singleton instance cache
_provider_instance: Optional[ObservabilityProvider] = None


def get_provider() -> ObservabilityProvider:
    """
    Get the configured observability provider.

    Returns a singleton instance based on OBSERVABILITY_PROVIDER environment variable.
    Subsequent calls return the same instance (provider is initialized once).

    Returns:
        ObservabilityProvider: The configured provider instance

    Environment Variables:
        OBSERVABILITY_PROVIDER: Which provider to use (datadog|sentry|disabled)

    Examples:
        # Using Datadog (default)
        OBSERVABILITY_PROVIDER=datadog
        provider = get_provider()  # Returns DatadogProvider

        # Using Sentry
        OBSERVABILITY_PROVIDER=sentry
        SENTRY_DSN=https://key@org.ingest.sentry.io/project
        provider = get_provider()  # Returns SentryProvider

        # Disabled (testing/development)
        OBSERVABILITY_PROVIDER=disabled
        provider = get_provider()  # Returns NoopProvider
    """
    global _provider_instance

    # Return cached instance if available
    if _provider_instance is not None:
        return _provider_instance

    # Determine which provider to use
    provider_name = os.getenv('OBSERVABILITY_PROVIDER', 'datadog').lower().strip()

    logger.info(f"Initializing observability provider: {provider_name}")

    # Create provider based on configuration
    if provider_name == 'datadog':
        _provider_instance = DatadogProvider()

    elif provider_name == 'sentry':
        _provider_instance = SentryProvider()

    elif provider_name in ('disabled', 'none', 'noop'):
        logger.info("Observability explicitly disabled")
        _provider_instance = NoopProvider()

    else:
        logger.warning(
            f"Unknown OBSERVABILITY_PROVIDER: '{provider_name}', "
            f"defaulting to Datadog. Valid options: datadog, sentry, disabled"
        )
        _provider_instance = DatadogProvider()

    logger.info(
        f"Provider initialized: {_provider_instance.name} "
        f"(enabled: {_provider_instance.is_enabled})"
    )

    return _provider_instance


def reset_provider() -> None:
    """
    Reset the provider singleton.

    Useful for testing when you need to switch providers within the same process.
    Should NOT be used in production code.
    """
    global _provider_instance
    _provider_instance = None
    logger.warning("Observability provider reset (should only be used in tests)")


# Export public API
__all__ = [
    'ObservabilityProvider',
    'get_provider',
    'reset_provider',
    'DatadogProvider',
    'SentryProvider',
    'NoopProvider',
]
