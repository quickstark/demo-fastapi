"""
MongoDB integration tests.
These tests require a MongoDB connection and are marked as integration tests.
"""

import json
import os
from unittest.mock import AsyncMock

import pytest

from src.mongo import *

print(os.getcwd())


@pytest.mark.integration
@pytest.mark.mongo
@pytest.mark.asyncio
async def test_get_one_mongo():
    """Test retrieving a single document from MongoDB."""
    # Call the async function and await its result
    response = await get_one_mongo("648b7444769c327f2a7cf0fe")

    assert isinstance(response, dict)
    expected_keys = {"name", "url", "ai_labels", "id"}
    assert expected_keys.issubset(response.keys())


@pytest.mark.integration
@pytest.mark.mongo
@pytest.mark.slow
@pytest.mark.asyncio
async def test_get_all_images_mongo():
    """Test retrieving all documents from MongoDB."""
    # Call the async function and await its result
    response = await get_all_images_mongo()

    # Assert that the response is an instance of Response
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
    assert "message" in response
    assert "Mongo added id:" in response["message"]


@pytest.mark.integration
@pytest.mark.mongo
@pytest.mark.asyncio
async def test_delete_one_mongo():
    """Test deleting a single document from MongoDB."""
    # First add a test document
    test_name = "test_delete"
    test_url = "https://example.com/delete.jpg"
    test_labels = ["delete", "test"]
    test_text = ["delete test"]
    
    add_response = await add_image_mongo(test_name, test_url, test_labels, test_text)
    
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
