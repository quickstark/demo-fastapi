from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from datadog import initialize, api
from ddtrace import patch_all, tracer
from ddtrace.constants import ERROR_MSG, ERROR_TYPE, ERROR_STACK
from ddtrace.profiling import Profiler
from ddtrace.debugging import DynamicInstrumentation
from ddtrace.runtime import RuntimeMetrics
import os
import traceback
import httpx
from pydantic import BaseModel

from src.amazon import *
from src.mongo import *
from src.openai import *
from src.postgres import *

RuntimeMetrics.enable()

# Load dotenv in the base root refers to application_top
APP_ROOT = os.path.join(os.path.dirname(__file__))
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)


# Define the origins that should be allowed to make requests to your API
origins = [
    "https://quickstark-vite-images.up.railway.app",
    "http://localhost:5173",  # Vite's default port
    "http://localhost:3000",  # Just in case you're using a different port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

# Instantiate the FastAPI app
app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include the routers
app.include_router(router_openai)
app.include_router(router_amazon)
app.include_router(router_mongo)
app.include_router(router_postgres)

# Define Python user-defined exceptions

class CustomError(Exception):
    """Base class for custom exceptions"""
    def __init__(self, message):
        self.message = message
        super().__init__(message)
        
    def report_to_datadog(self):
        """Report the error to Datadog."""
        span = tracer.current_span()
        if span is not None:
            # Tagging the current span with error information
            span.set_tag(ERROR_MSG, self.message)
            span.set_tag(ERROR_TYPE, type(self).__name__)
            span.set_tag(ERROR_STACK, traceback.format_exc())
            span.set_tag("custom.status", "error_detected")
            span.error = 1

# Add this class for the request body
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
    with tracer.trace("custom.error.example"):
        try:
            if amazon_error_text(amztext):
                error_message = f"Image Text Error - {' '.join(amztext)}"
                raise CustomError(error_message)
        except CustomError as e:
            # Handle the exception and report to Datadog
            e.report_to_datadog()

    # Check if the image labels contained the word "bug" or "insect" and issue an error
    with tracer.trace("custom.error.bug"):
        try:
            if amazon_error_label(amzlabels):
                error_message = f"Image Label Error - {' '.join(amzlabels)}"
                raise CustomError(error_message)
        except CustomError as e:
            # Handle the exception and report to Datadog
            e.report_to_datadog()

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

# Initialize tracing before anything else
patch_all()

# Configure the tracer explicitly
tracer.configure(
    hostname=os.getenv('DD_AGENT_HOST', 'datadog-agent'),
    port=int(os.getenv('DD_AGENT_PORT', '8126'))
)

# Initialize profiler
profiler = Profiler()
profiler.start()

# DynamicInstrumentation.enable()
