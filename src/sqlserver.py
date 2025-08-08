"""
Functions for interacting with SQL Server.
"""

import os
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import List, Optional

try:
    import pytds
    PYTDS_AVAILABLE = True
except ImportError as e:
    pytds = None
    PYTDS_AVAILABLE = False
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"pytds not available: {e}. SQL Server functionality will be disabled.")

from dotenv import load_dotenv
from fastapi import APIRouter, Response, encoders
from pydantic import BaseModel
from ddtrace.trace import Pin
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Load dotenv in the base root refers to application_top
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

# Prep our environment variables / upload .env to Railway.app
SQLSERVER_HOST = os.getenv('SQLSERVERHOST')
SQLSERVER_PORT = int(os.getenv('SQLSERVERPORT', '1433'))
SQLSERVER_USER = os.getenv('SQLSERVERUSER')
SQLSERVER_PW = os.getenv('SQLSERVERPW')
SQLSERVER_DB = os.getenv('SQLSERVERDB')

# Connection parameters for pytds (pure Python)
CONNECTION_PARAMS = {
    'server': SQLSERVER_HOST,
    'port': SQLSERVER_PORT,
    'database': SQLSERVER_DB,
    'user': SQLSERVER_USER,
    'password': SQLSERVER_PW,
    'timeout': 30,
    'login_timeout': 30
    # Note: tds_version auto-negotiated by default (best practice)
}

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=10)

# Global connection (will be managed similar to postgres.py pattern)
conn = None

def get_connection():
    """Get or create SQL Server connection."""
    if not PYTDS_AVAILABLE:
        logger.error("pytds is not available. SQL Server connection cannot be established.")
        return None
        
    global conn
    try:
        if conn is None or (hasattr(conn, 'is_connected') and not conn.is_connected()):
            logger.info(f"Attempting to connect to SQL Server: server={SQLSERVER_HOST}:{SQLSERVER_PORT} database={SQLSERVER_DB} user={SQLSERVER_USER}")
            conn = pytds.connect(**CONNECTION_PARAMS)
            # Configure the connection with the proper service name for Database Monitoring
            Pin.override(conn, service="sqlserver")
            logger.info(f"Successfully connected to SQL Server database: {SQLSERVER_DB} at {SQLSERVER_HOST}:{SQLSERVER_PORT}")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to SQL Server: {e}", exc_info=True)
        conn = None
        return None

# Initialize connection on module load
if PYTDS_AVAILABLE:
    try:
        get_connection()
    except Exception as e:
        logger.error(f"Failed to initialize SQL Server connection: {e}")
else:
    logger.warning("pytds not available - SQL Server functionality disabled")

# Create a new router for SQL Server Routes
router_sqlserver = APIRouter()

class ImageModel(BaseModel):
    """Pydantic model for image data stored in SQL Server.
    
    Attributes:
        id (int): Unique identifier for the image.
        name (str): Original filename of the image.
        width (Optional[int]): Image width in pixels.
        height (Optional[int]): Image height in pixels.
        url (Optional[str]): S3 URL of the original image.
        url_resize (Optional[str]): S3 URL of resized version.
        date_added (Optional[date]): Date image was added to database.
        date_identified (Optional[date]): Date AI analysis was performed.
        ai_labels (Optional[list]): AI-detected labels from image analysis.
        ai_text (Optional[list]): AI-extracted text from image.
    """
    id: int
    name: str
    width: Optional[int]
    height: Optional[int]
    url: Optional[str]
    url_resize: Optional[str]
    date_added: Optional[date]
    date_identified: Optional[date]
    ai_labels: Optional[list]
    ai_text: Optional[list]


async def execute_query_async(query: str, params: tuple = None):
    """Execute SELECT query asynchronously using thread pool."""
    def _execute():
        connection = get_connection()
        if connection is None:
            raise Exception("Failed to get SQL Server connection")
        
        cursor = connection.cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
    
    return await asyncio.get_event_loop().run_in_executor(executor, _execute)


async def execute_non_query_async(query: str, params: tuple = None):
    """Execute INSERT/UPDATE/DELETE query asynchronously using thread pool."""
    def _execute():
        connection = get_connection()
        if connection is None:
            raise Exception("Failed to get SQL Server connection")
        
        cursor = connection.cursor()
        try:
            cursor.execute(query, params or ())
            connection.commit()
            return cursor.rowcount
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()
    
    return await asyncio.get_event_loop().run_in_executor(executor, _execute)


@router_sqlserver.get("/get-image-sqlserver/{id}", response_model=ImageModel, response_model_exclude_unset=True)
async def get_image_sqlserver(id: int):
    """
    Fetch a single image from the SQL Server database.

    Args:
        id (int): The ID of the image to fetch.

    Returns:
        ImageModel: The image data as an ImageModel instance.
    """
    try:
        query = "SELECT id, name, width, height, url, url_resize, date_added, date_identified, ai_labels, ai_text FROM images WHERE id = ?"
        result = await execute_query_async(query, (id,))
        
        if not result:
            return {"error": "Image not found"}
            
        row = result[0]
        logger.debug(f"Fetched Image SQL Server: {row[1]}")
        
        # Parse JSON fields
        ai_labels = json.loads(row[8]) if row[8] else []
        ai_text = json.loads(row[9]) if row[9] else []
        
        item = ImageModel(
            id=row[0], 
            name=row[1], 
            width=row[2], 
            height=row[3], 
            url=row[4],
            url_resize=row[5], 
            date_added=row[6], 
            date_identified=row[7], 
            ai_labels=ai_labels, 
            ai_text=ai_text
        )
        return item.model_dump()
        
    except Exception as err:
        logger.error(f"Error in get_image_sqlserver: {err}", exc_info=True)
        return {"error": str(err)}


async def get_all_images_sqlserver(response_model=List[ImageModel]):
    """
    Fetch all images from the SQL Server database.

    Returns:
        List[ImageModel]: A list of images as ImageModel instances.
    """
    formatted_photos = []
    try:
        query = "SELECT id, name, width, height, url, url_resize, date_added, date_identified, ai_labels, ai_text FROM images ORDER BY id DESC"
        result = await execute_query_async(query)
        
        for row in result:
            # Parse JSON fields
            ai_labels = json.loads(row[8]) if row[8] else []
            ai_text = json.loads(row[9]) if row[9] else []
            
            formatted_photos.append(
                ImageModel(
                    id=row[0], 
                    name=row[1], 
                    width=row[2], 
                    height=row[3], 
                    url=row[4],
                    url_resize=row[5], 
                    date_added=row[6], 
                    date_identified=row[7], 
                    ai_labels=ai_labels, 
                    ai_text=ai_text
                )
            )
            
    except Exception as err:
        logger.error(f"Error in get_all_images_sqlserver: {err}", exc_info=True)
    
    return formatted_photos


async def add_image_sqlserver(name: str, url: str, ai_labels: list, ai_text: list):
    """
    Add an image and its metadata to the SQL Server database.

    Args:
        name (str): The name of the image.
        url (str): The S3 URL of the image.
        ai_labels (list): Labels identified by Amazon Rekognition.
        ai_text (list): Text identified by Amazon Rekognition.
    """
    try:
        # Ensure we have valid lists for JSON conversion
        if not isinstance(ai_labels, list):
            ai_labels = []
        if not isinstance(ai_text, list):
            ai_text = []
            
        # Ensure each element is a string
        ai_labels = [str(label) for label in ai_labels]
        ai_text = [str(text) for text in ai_text]
        
        logger.debug(f"Adding image to SQL Server - AI Labels: {ai_labels}")
        logger.debug(f"Adding image to SQL Server - AI Text: {ai_text}")
        
        # Convert Python lists to JSON strings
        ai_labels_json = json.dumps(ai_labels)
        ai_text_json = json.dumps(ai_text)
        
        query = "INSERT INTO images (name, url, ai_labels, ai_text) VALUES (?, ?, ?, ?)"
        params = (name, url, ai_labels_json, ai_text_json)
        
        await execute_non_query_async(query, params)
        return {"message": f"Image {name} added successfully"}
        
    except Exception as err:
        logger.error(f"Error in add_image_sqlserver: {err}", exc_info=True)
        return {"error": str(err)}


async def delete_image_sqlserver(id: int):
    """
    Delete an image from the SQL Server database.

    Args:
        id (int): The ID of the image to delete.
    """
    try:
        query = "DELETE FROM images WHERE id = ?"
        rows_affected = await execute_non_query_async(query, (id,))
        
        if rows_affected == 0:
            return {"message": f"No image with id {id} found to delete"}
        return {"message": f"Image with id {id} deleted successfully"}
        
    except Exception as err:
        logger.error(f"Error in delete_image_sqlserver: {err}", exc_info=True)
        return {"error": str(err)}