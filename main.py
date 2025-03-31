# System imports
import os
import logging
import traceback
import asyncio

# Set environment variables before any Datadog imports
os.environ["DD_LLMOBS_ML_APP"] = "youtube-summarizer"
os.environ["DD_LLMOBS_EVALUATORS"] = "ragas_faithfulness,ragas_context_precision,ragas_answer_relevancy"

# Load environment variables
from dotenv import load_dotenv
APP_ROOT = os.path.join(os.path.dirname(__file__))
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import all modules that need to be instrumented BEFORE patching
import httpx
import boto3
import pymongo
import psycopg
import openai  # Important for LLM observability

# Now initialize Datadog tracing
from ddtrace import patch_all, tracer
from ddtrace.llmobs import LLMObs
from ddtrace.constants import ERROR_MSG, ERROR_TYPE, ERROR_STACK
from ddtrace.runtime import RuntimeMetrics

# Use verbose logging to see what's being patched
logger.info("Initializing Datadog tracing...")
patch_all(logging=True, httpx=True, pymongo=True, psycopg=True, boto=True, openai=True, fastapi=True)
logger.info("Datadog tracing initialized")

# Initialize LLM Observability
LLMObs.enable()
logger.info("LLM Observability enabled")

# Enable runtime metrics
RuntimeMetrics.enable()
logger.info("Runtime metrics enabled")

# Now initialize FastAPI (after patching)
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(debug=True)

# Now import application modules (after patching)
from src.amazon import *
from src.mongo import *
from src.postgres import *
from src.openai import *

# Define CORS origins
origins = [
    "http://localhost:5173",  # Vite's default port
    "http://localhost:3000",  # Just in case you're using a different port
    "http://localhost:5174",  # Local development
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://192.168.1.100:3000",
    "http://192.168.1.100:5173",
    "http://192.168.1.61:5174",  # Your development IP
    "*",                          # Allow all origins (only for development!)
]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize other services
logger.info("Initializing application services...")

# Include the routers
try:
    app.include_router(router_openai)
    logger.info("OpenAI router initialized")
    app.include_router(router_amazon)
    logger.info("Amazon router initialized")
    app.include_router(router_mongo)
    logger.info("MongoDB router initialized")
    app.include_router(router_postgres)
    logger.info("PostgreSQL router initialized")
except Exception as e:
    logger.error(f"Error initializing routers: {e}")

# Initialize Datadog tracer with error handling
try:
    tracer.configure()
    logger.info("Datadog tracer configured")
except Exception as e:
    logger.error(f"Warning: Could not configure tracer: {e}")

# Request body model class
class Post(BaseModel):
    title: str
    body: str
    userId: int

@app.get("/images")
async def get_all_images(backend: str = "mongo"):
    """
    Retrieve all images from the specified backend.

    Args:
        backend (str): The backend to fetch images from. Defaults to "mongo".

    Returns:
        List[dict]: A list of images.
    """
    print(f"Getting all images from {backend}")
    if backend == "mongo":
        images = await get_all_images_mongo()
    elif backend == "postgres":
        images = await get_all_images_postgres()
    else:
        raise CustomError("Invalid backend specified")
    return images

@app.post("/add_image", status_code=201)
async def add_photo(file: UploadFile, backend: str = "mongo"):
    """
    Upload an image to Amazon S3 and store metadata in the specified backend.

    Args:
        file (UploadFile): The image file to upload.
        backend (str): The backend to store image metadata. Defaults to "mongo".

    Returns:
        dict: A message indicating the result of the operation.
    """
    print(f"Uploading File ${file.filename} - ${file.content_type}")

    # Attempt to upload the image to Amazon S3
    try:
        s3_url = amazon_upload(file)
        # check if the file url is null
        if s3_url is None:
            raise CustomError("Error uploading image to Amazon S3")
    except CustomError as err:
        print(err)

    # Attempt to detect labels and text in the image using Amazon Rekognition
    try:
        # amazon_detection(file) returns a tuple of 3 lists
        amzlabels, amztext, amzmoderation = amazon_detection(file)
        if not amzlabels and not amztext and not amzmoderation:
            raise CustomError("Error processing Amazon Rekognition")
    except CustomError as err:
        print(err)

    # Check the image for questionable content using Amazon Rekognition
    try:
        if amazon_moderation(amzmoderation):
            return {"message": f"{file.filename} may contain questionable content. Let's keep it family friendly. ;-)"}
            raise CustomError("We detected inappropriate content")
    except CustomError as err:
        print(err)

    # Check if the image contained the word "error" and issue an error
    try:
        if amazon_error_text(amztext):
            error_message = f"Image Text Error - {' '.join(amztext)}"
            raise CustomError(error_message)
    except CustomError as e:
        # Handle the exception but don't report to Datadog
        print(f"Error: {str(e)}")

    # Check if the image labels contained the word "bug" or "insect" and issue an error
    try:
        if amazon_error_label(amzlabels):
            error_message = f"Image Label Error - {' '.join(amzlabels)}"
            raise CustomError(error_message)
    except CustomError as e:
        # Handle the exception but don't report to Datadog
        print(f"Error: {str(e)}")

    if backend == "mongo":
        # Attempt to upload the image to MongoDB
        print("Adding image to MongoDB")
        try:
            await add_image_mongo(file.filename, s3_url, amzlabels, amztext)
        except CustomError as err:
            print(err)
    elif backend == "postgres":
        # Attempt to upload the image to Postgres
        try:
            await add_image_postgres(file.filename, s3_url, amzlabels, amztext)
        except CustomError as err:
            print(err)
    else:
        raise CustomError("Backend not supported")

@app.delete("/delete_image/{id}", status_code=201)
async def delete_image(id, backend: str = "mongo"):
    """
    Delete an image from the specified backend and Amazon S3.

    Args:
        id (str): The ID of the image to delete.
        backend (str): The backend to delete the image from. Defaults to "mongo".

    Returns:
        dict: A message indicating the result of the operation.
    """
    print(f"Attempt to Delete File {id} from {backend}")

    if backend == "mongo":
        # Attempt to delete the image from MongoDB
        try:
            image = await get_one_mongo(id)
            res = await delete_one_mongo(id)
        except CustomError as err:
            print(err)
    elif backend == "postgres":
        # Attempt to delete the image from Postgres
        try:
            image = await get_image_postgres(id)
            res = await delete_image_postgres(id)
        except CustomError as err:
            print(err)
    else:
        raise CustomError("Backend not supported")

    # Attempt to delete the image from Amazon S3
    try:
        print(image)
        res = await amazon_delete_one_s3(image["name"])
        print(res)
    except CustomError as err:
        print(err)

@app.post("/create_post")
@tracer.wrap()
async def create_post(post: Post):
    with tracer.trace("create_post_request"):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://jsonplaceholder.typicode.com/posts',
                json={
                    'title': post.title,
                    'body': post.body,
                    'userId': post.userId
                }
            )
            return response.json()

@app.get("/")
async def root():
    """
    Root endpoint of the FastAPI application.

    Returns:
        dict: A welcome message.
    """
    return {"message": "Welcome to FastAPI!"}

@app.get("/timeout-test")
@tracer.wrap()
async def timeout_test(timeout: int = 0):
    """
    Test endpoint that delays response by the specified timeout in seconds.
    
    Args:
        timeout (int): Number of seconds to delay the response. Defaults to 0.
        
    Returns:
        dict: A message indicating the timeout value used.
    """
    with tracer.trace("timeout_test"):
        # Add a span tag to track the requested timeout
        span = tracer.current_span()
        if span:
            span.set_tag("timeout.requested_seconds", timeout)
        
        # Sleep for the specified number of seconds
        if timeout > 0:
            await asyncio.sleep(timeout)
            
        return {
            "message": f"Response after {timeout} seconds delay",
            "timeout_value": timeout
        }
