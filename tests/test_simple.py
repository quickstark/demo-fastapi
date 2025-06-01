"""
Simple unit tests that don't require external dependencies.
These tests demonstrate pytest is working correctly.
"""

import pytest


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


@pytest.mark.unit
def test_list_operations():
    """Test basic list operations."""
    test_list = [1, 2, 3, 4, 5]
    assert len(test_list) == 5
    assert test_list[0] == 1
    assert test_list[-1] == 5
    assert 3 in test_list
    assert 6 not in test_list


@pytest.mark.unit
def test_dictionary_operations():
    """Test basic dictionary operations."""
    test_dict = {"name": "test", "value": 42}
    assert test_dict["name"] == "test"
    assert test_dict["value"] == 42
    assert "name" in test_dict
    assert "missing" not in test_dict


@pytest.mark.unit
def test_environment_variables():
    """Test that we can access environment variables."""
    import os
    
    # Test that we can access environment variables
    # (They might be empty in test, but should be accessible)
    dd_service = os.environ.get('DD_SERVICE', 'test-service')
    dd_env = os.environ.get('DD_ENV', 'test')
    
    assert isinstance(dd_service, str)
    assert isinstance(dd_env, str)
    assert len(dd_service) > 0
    assert len(dd_env) > 0 