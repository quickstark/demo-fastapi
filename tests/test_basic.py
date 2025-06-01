"""
Basic unit tests for the FastAPI application.
These tests don't require external dependencies and run quickly.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.mark.unit
def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


@pytest.mark.unit
def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.unit
def test_app_creation():
    """Test that the FastAPI app can be created."""
    assert app is not None
    assert hasattr(app, 'routes')
    assert len(app.routes) > 0


@pytest.mark.unit
def test_environment_variables():
    """Test that critical environment variables can be accessed."""
    # These should be set in the test environment
    import os
    
    # Test that we can access environment variables
    # (They might be empty in test, but should be accessible)
    dd_service = os.environ.get('DD_SERVICE', 'test-service')
    dd_env = os.environ.get('DD_ENV', 'test')
    
    assert isinstance(dd_service, str)
    assert isinstance(dd_env, str)


@pytest.mark.unit
def test_basic_math():
    """Simple test to verify pytest is working."""
    assert 1 + 1 == 2
    assert 2 * 3 == 6
    assert 10 / 2 == 5.0


@pytest.mark.unit
def test_string_operations():
    """Test basic string operations."""
    test_string = "Hello, Datadog!"
    assert test_string.startswith("Hello")
    assert test_string.endswith("!")
    assert "Datadog" in test_string
    assert len(test_string) > 0 