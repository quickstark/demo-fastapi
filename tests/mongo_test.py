"""
MongoDB integration tests.
These tests require a MongoDB connection and are marked as integration tests.
When MongoDB is not available, they test graceful degradation behavior.
"""

import json
import os
from unittest.mock import AsyncMock

import pytest

from src.mongo import *

print(os.getcwd())


def is_mongo_available():
    """Check if MongoDB is available for testing."""
    return is_mongo_configured() and get_mongo_client() is not None


@pytest.mark.integration
@pytest.mark.mongo
@pytest.mark.asyncio
async def test_get_one_mongo():
    """Test retrieving a single document from MongoDB."""
    # Call the async function and await its result
    response = await get_one_mongo("507f1f77bcf86cd799439011")  # Valid ObjectId format
    
    # The response should always be a dict
    assert isinstance(response, dict)
    
    if is_mongo_available():
        # When MongoDB is available, we should get either:
        # 1. A document with expected keys, or 
        # 2. A "not found" error (since we're using a fake ID)
        if "error" in response:
            # Document not found (expected with fake ID)
            assert "not found" in response["error"].lower() or "failed to fetch" in response["error"].lower()
        else:
            # Document found - check for expected keys
            expected_keys = {"ai_labels", "id", "name", "url"}
            assert expected_keys.issubset(response.keys())
    else:
        # When MongoDB is not available, should get unavailable error
        assert response == {"error": "MongoDB not available"}


@pytest.mark.integration
@pytest.mark.mongo
@pytest.mark.slow
@pytest.mark.asyncio
async def test_get_all_images_mongo():
    """Test retrieving all documents from MongoDB."""
    # Call the async function and await its result
    response = await get_all_images_mongo()

    if is_mongo_available():
        # When MongoDB is available, expect Response object
        assert isinstance(response, Response)

        # Get the content of the response
        response_content = json.loads(response.body)

        # Assert that the response content is a list
        assert isinstance(response_content, list)

        # Check if the list contains dictionaries
        for item in response_content:
            assert isinstance(item, dict)
            expected_keys = {"name", "url", "ai_labels", "ai_text", "id"}
            assert expected_keys.issubset(item.keys())
    else:
        # When MongoDB is not available, expect error dict
        assert isinstance(response, dict)
        assert "error" in response
        assert response["error"] == "MongoDB not available"


@pytest.mark.integration
@pytest.mark.mongo
@pytest.mark.asyncio
async def test_add_image_mongo():
    """Test adding a new image document to MongoDB."""
    test_name = "test_image"
    test_url = "https://example.com/test.jpg"
    test_labels = ["test", "image"]
    test_text = ["test text"]
    
    response = await add_image_mongo(test_name, test_url, test_labels, test_text)
    
    assert isinstance(response, dict)
    
    if is_mongo_available():
        # When MongoDB is available, expect success message
        assert "message" in response
        assert "Mongo added id:" in response["message"]
    else:
        # When MongoDB is not available, expect error
        assert "error" in response
        assert response["error"] == "MongoDB not available"


@pytest.mark.integration
@pytest.mark.mongo
@pytest.mark.asyncio
async def test_delete_one_mongo():
    """Test deleting a single document from MongoDB."""
    if not is_mongo_available():
        # Test graceful degradation when MongoDB is not available
        response = await delete_one_mongo("648b7444769c327f2a7cf0fe")
        assert isinstance(response, dict)
        assert "error" in response
        assert response["error"] == "MongoDB not available"
        return
    
    # When MongoDB is available, test full functionality
    # First add a test document
    test_name = "test_delete"
    test_url = "https://example.com/delete.jpg"
    test_labels = ["delete", "test"]
    test_text = ["delete test"]
    
    add_response = await add_image_mongo(test_name, test_url, test_labels, test_text)
    
    # Check if add was successful
    if "error" in add_response:
        pytest.skip("Cannot test delete without successful add")
    
    # Extract the ID from the response
    message = add_response["message"]
    # Parse the ObjectId from the message
    import re
    id_match = re.search(r'Mongo added id: (.+)', message)
    if id_match:
        test_id = id_match.group(1)
        
        # Now delete the document
        delete_response = await delete_one_mongo(test_id)
        
        assert isinstance(delete_response, dict)
        assert "message" in delete_response
        assert "deleted" in delete_response["message"]


@pytest.mark.integration
@pytest.mark.mongo
@pytest.mark.asyncio
async def test_mongo_graceful_degradation():
    """Test that MongoDB functions handle unavailable database gracefully."""
    # This test specifically verifies graceful degradation behavior
    # It should pass whether MongoDB is available or not
    
    # Test that config check works
    config = get_mongo_config()
    assert isinstance(config, dict)
    assert "MONGO_CONN" in config
    assert "MONGO_USER" in config
    assert "MONGO_PW" in config
    
    # Test that configuration detection works
    is_configured = is_mongo_configured()
    assert isinstance(is_configured, bool)
    
    # Test that client getter doesn't crash
    client = get_mongo_client()
    # Client should be either MongoClient instance or None
    assert client is None or hasattr(client, 'admin')
    
    # Test that database getter doesn't crash
    db = get_mongo_db()
    assert db is None or hasattr(db, 'name')
    
    # Test that collection getter doesn't crash
    collection = get_mongo_collection()
    assert collection is None or hasattr(collection, 'name')
