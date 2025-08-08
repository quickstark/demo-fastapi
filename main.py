# System imports
import os
import logging
import traceback
import asyncio

# Set up logging FIRST (before any other code uses logger)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("Logging configured.")

# Set environment variables before any Datadog imports
os.environ["DD_LLMOBS_ML_APP"] = "youtube-summarizer"
os.environ["DD_LLMOBS_EVALUATORS"] = "ragas_faithfulness,ragas_context_precision,ragas_answer_relevancy"

logger.info(f"Set LLM Observability app name: {os.environ['DD_LLMOBS_ML_APP']}")
logger.info(f"Set LLM Observability evaluators: {os.environ['DD_LLMOBS_EVALUATORS']}")

# Load environment variables
from dotenv import load_dotenv
APP_ROOT = os.path.join(os.path.dirname(__file__))
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)
logger.info("Environment variables loaded from .env")

# Define CustomError class for application-specific exceptions
class CustomError(Exception):
    """Custom exception class for application-specific errors."""
    
    def __init__(self, message, error_type=None, tags=None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type or "application_error"
        self.tags = tags or []
        
        # Get Datadog service information from environment variables
        dd_service = os.getenv('DD_SERVICE', 'fastapi-app')
        dd_env = os.getenv('DD_ENV', 'dev')
        dd_version = os.getenv('DD_VERSION', '1.0')
        
        # Record the error in Datadog if tracer is available
        try:
            # Ensure tracer is imported before use if needed here
            from ddtrace import tracer, ERROR_MSG, ERROR_TYPE, ERROR_STACK
            span = tracer.current_span()
            if span:
                span.error = 1
                span.set_tag(ERROR_MSG, message)
                span.set_tag(ERROR_TYPE, self.error_type)
                span.set_tag(ERROR_STACK, traceback.format_exc())
                
                # Add service information tags
                span.set_tag("service", dd_service)
                span.set_tag("env", dd_env)
                span.set_tag("version", dd_version)
                
                # Add any custom tags
                for tag in self.tags:
                    if isinstance(tag, tuple) and len(tag) == 2:
                        span.set_tag(tag[0], tag[1])
                    elif isinstance(tag, str):
                        span.set_tag(tag, True)
                
                logger.error(f"CustomError Recorded: {message}") # Changed log message slightly
        except Exception as e:
            logger.error(f"Failed to record CustomError in Datadog: {e}")

# Import all modules that need to be instrumented BEFORE patching
import httpx
import boto3
import pymongo
import psycopg
import openai  # Important for LLM observability

# Now initialize Datadog tracing
from ddtrace import patch_all, tracer
# ERROR_MSG, ERROR_TYPE, ERROR_STACK moved to CustomError
from ddtrace.runtime import RuntimeMetrics

# Use verbose logging to see what's being patched
logger.info("Initializing Datadog tracing...")
patch_all(logging=True, httpx=True, pymongo=True, psycopg=True, boto=True, openai=True, fastapi=True)
logger.info("Datadog tracing initialized")

# Conditionally initialize LLM Observability based on environment variable
llmobs_enabled = (os.getenv('DD_LLMOBS_ENABLED', 'true').lower() == 'true' and 
                  os.getenv('DD_LLMOBS_EVALUATORS_ENABLED', 'true').lower() == 'true')
if llmobs_enabled:
    try:
        from ddtrace.llmobs import LLMObs
        LLMObs.enable()
        logger.info("LLM Observability enabled")
    except Exception as e:
        logger.warning(f"Failed to enable LLM Observability: {e}")
        logger.info("Continuing without LLM Observability")
else:
    logger.info("LLM Observability disabled via environment variables")

# Enable runtime metrics
RuntimeMetrics.enable()
logger.info("Runtime metrics enabled")

# Enable Datadog profiling (conditional based on environment variable)
profiler_enabled = os.getenv('DD_PROFILING_ENABLED', 'true').lower() == 'true'
if profiler_enabled:
    try:
        from ddtrace.profiling import Profiler
        prof = Profiler()
        prof.start()
        logger.info("Datadog profiler enabled and started")
    except Exception as e:
        logger.warning(f"Failed to enable Datadog profiler: {e}")
        logger.info("Continuing without profiler")
else:
    logger.info("Datadog profiler disabled via environment variables")

# Now initialize FastAPI (after patching)
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(debug=True)

# Now import application modules (after patching)
from src.amazon import *
from src.mongo import *
from src.postgres import *
from src.sqlserver import *
from src.openai_service import router_openai, YouTubeRequest, summarize_youtube_video
from src.datadog import *  # Import the new Datadog module
from src.datadog import app_event, bug_detection_event  # Explicit imports for error tracking

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
logger.info("CORS middleware configured.")

# Initialize other services
logger.info("Initializing application services and routers...")

# Include the routers
try:
    app.include_router(router_openai, prefix="/api/v1", tags=["OpenAI"])
    logger.info("OpenAI router included.")
    app.include_router(router_amazon, prefix="/api/v1", tags=["Amazon S3"])
    logger.info("Amazon router included.")
    app.include_router(router_mongo, prefix="/api/v1", tags=["MongoDB"])
    logger.info("MongoDB router included.")
    app.include_router(router_postgres, prefix="/api/v1", tags=["PostgreSQL"])
    logger.info("PostgreSQL router included.")
    app.include_router(router_sqlserver, prefix="/api/v1", tags=["SQL Server"])
    logger.info("SQL Server router included.")
    app.include_router(router_datadog)  # Include the new Datadog router
    logger.info("Datadog router included.")
except Exception as e:
    logger.error(f"Error including routers: {e}")

# Initialize Datadog tracer with error handling
# Note: tracer.configure() might be redundant if DD_AGENT_HOST/DD_TRACE_AGENT_PORT are set
try:
    # tracer.configure() # Often not needed if env vars are set
    logger.info("Datadog tracer configuration checked (using env vars or defaults).")
except Exception as e:
    logger.error(f"Warning: Problem during tracer configuration check: {e}")

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
    logger.info(f"Getting all images from {backend}")
    if backend == "mongo":
        images = await get_all_images_mongo()
    elif backend == "postgres":
        images = await get_all_images_postgres()
    elif backend == "sqlserver":
        images = await get_all_images_sqlserver()
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
    logger.info(f"Uploading File {file.filename} - {file.content_type}")
    
    # Variables to store image data
    s3_url = None
    amzlabels = []
    amztext = []
    amzmoderation = []
    result = None

    # Attempt to upload the image to Amazon S3
    try:
        s3_url = amazon_upload(file)
        # check if the file url is null
        if s3_url is None:
            error_tags = [
                ("error.source", "s3"),
                ("error.type", "upload_failure"),
                ("error.filename", file.filename)
            ]
            raise CustomError(
                message="Error uploading image to Amazon S3",
                error_type="s3_upload_failure",
                tags=error_tags
            )
    except CustomError as e:
        # Now properly log the error to Datadog
        logger.error(f"S3 upload error: {str(e)}")
        # Return a proper error response to the client
        return {"error": str(e), "type": "s3_upload_error", "filename": file.filename}

    # Attempt to detect labels and text in the image using Amazon Rekognition
    try:
        # amazon_detection(file) returns a tuple of 3 lists
        amzlabels, amztext, amzmoderation = amazon_detection(file)
        if not amzlabels and not amztext and not amzmoderation:
            error_tags = [
                ("error.source", "rekognition"),
                ("error.type", "detection_failure"),
                ("error.filename", file.filename)
            ]
            raise CustomError(
                message="Error processing Amazon Rekognition",
                error_type="rekognition_failure",
                tags=error_tags
            )
    except CustomError as e:
        # Now properly log the error to Datadog
        logger.error(f"Rekognition error: {str(e)}")
        # Return a proper error response to the client
        return {"error": str(e), "type": "rekognition_error", "filename": file.filename}

    # Save image data to database first, before checking for moderation/errors
    if backend == "mongo":
        # Attempt to upload the image to MongoDB
        logger.info("Adding image to MongoDB")
        try:
            result = await add_image_mongo(file.filename, s3_url, amzlabels, amztext)
            logger.info(f"Successfully saved image {file.filename} to MongoDB")
        except Exception as e:
            logger.error(f"MongoDB storage error: {str(e)}")
            return {"error": str(e), "type": "mongodb_error", "filename": file.filename}
    elif backend == "postgres":
        # Attempt to upload the image to Postgres
        try:
            result = await add_image_postgres(file.filename, s3_url, amzlabels, amztext)
            logger.info(f"Successfully saved image {file.filename} to PostgreSQL")
        except Exception as e:
            logger.error(f"PostgreSQL storage error: {str(e)}")
            return {"error": str(e), "type": "postgres_error", "filename": file.filename}
    elif backend == "sqlserver":
        # Attempt to upload the image to SQL Server
        try:
            result = await add_image_sqlserver(file.filename, s3_url, amzlabels, amztext)
            logger.info(f"Successfully saved image {file.filename} to SQL Server")
        except Exception as e:
            logger.error(f"SQL Server storage error: {str(e)}")
            return {"error": str(e), "type": "sqlserver_error", "filename": file.filename}
    else:
        error_tags = [
            ("error.source", "backend_selection"),
            ("error.type", "invalid_backend"),
            ("error.backend", backend)
        ]
        error = CustomError(
            message="Backend not supported",
            error_type="invalid_backend",
            tags=error_tags
        )
        logger.error(f"Backend error: {str(error)}")
        return {"error": str(error), "type": "backend_error", "backend": backend}

    # Now check for moderation issues - image is already saved
    response_data = {"message": f"Image {file.filename} uploaded successfully", "database_result": result}
    moderation_triggered = False
    error_text_triggered = False
    bug_detected_triggered = False

    # Check the image for questionable content using Amazon Rekognition
    try:
        if amazon_moderation(amzmoderation):
            error_message = f"{file.filename} may contain questionable content. Let's keep it family friendly. ;-)"
            # Create a list of tags for the error, including moderation labels
            error_tags = [
                ("error.source", "rekognition"),
                ("error.type", "content_moderation"),
                ("error.moderation_labels", ", ".join(amzmoderation)),
                ("error.filename", file.filename)
            ]
            
            # Send explicit event to Datadog using our new function
            try:
                # Call the bug_detection_event function with moderation type
                await bug_detection_event(
                    filename=file.filename,
                    labels=amzmoderation,
                    detection_type="moderation",
                    additional_info=f"Content moderation triggered for image: {', '.join(amzmoderation)}"
                )
                logger.info(f"Content moderation event sent to Datadog for {file.filename}")
                
                # Also send to Datadog's warning events using app_event
                try:
                    await app_event(
                        event_type="warning",
                        message=f"Content moderation triggered for image: {file.filename}. Content: {', '.join(amzmoderation)}"
                    )
                    logger.info(f"Moderation warning event sent to Datadog via app_event for {file.filename}")
                except Exception as app_event_error:
                    logger.error(f"Failed to send moderation warning via app_event to Datadog: {app_event_error}")
                
            except Exception as event_error:
                logger.error(f"Failed to send content moderation event to Datadog: {event_error}")
            
            moderation_triggered = True
            response_data["warning"] = error_message
            response_data["type"] = "moderation_triggered"
            response_data["moderation_labels"] = amzmoderation
    except Exception as e:
        # Log the error to Datadog but don't return an error response
        logger.error(f"Content moderation check error: {str(e)}")

    # Check if the image contained the word "error" and issue an error
    try:
        if amazon_error_text(amztext):
            error_message = f"Image Text Error - {' '.join(amztext)}"
            # Create a list of tags for the error, including all detected text
            error_tags = [
                ("error.source", "rekognition"),
                ("error.type", "error_text_detection"),
                ("error.text", ", ".join(amztext)),
                ("error.filename", file.filename)
            ]
            
            # Send explicit event to Datadog using our new function
            try:
                # Call the bug_detection_event function with error_text type
                await bug_detection_event(
                    filename=file.filename,
                    labels=amztext,
                    detection_type="error_text",
                    additional_info=f"Error text detected in image: {', '.join(amztext)}"
                )
                logger.info(f"Error text detection event sent to Datadog for {file.filename}")
                
                # Also send to Datadog's error events using app_event
                try:
                    await app_event(
                        event_type="error",
                        message=f"Error text detected in image: {file.filename}. Text: {', '.join(amztext)}"
                    )
                    logger.info(f"Error text event sent to Datadog via app_event for {file.filename}")
                except Exception as app_event_error:
                    logger.error(f"Failed to send error text via app_event to Datadog: {app_event_error}")
                
            except Exception as event_error:
                logger.error(f"Failed to send error text detection event to Datadog: {event_error}")
            
            error_text_triggered = True
            response_data["warning"] = error_message
            response_data["type"] = "error_text_detected"
            response_data["text"] = amztext
    except Exception as e:
        # Log the error to Datadog but don't return an error response
        logger.error(f"Text error detection check error: {str(e)}")

    # Check if the image labels contained the word "bug" or "insect" and issue an error
    try:
        if amazon_error_label(amzlabels):
            error_message = f"Image Label Error - {' '.join(amzlabels)}"
            # Create a list of tags for the error, including all the labels
            error_tags = [
                ("error.source", "rekognition"),
                ("error.type", "bug_detection"),
                ("error.labels", ", ".join(amzlabels)),
                ("error.filename", file.filename)
            ]
            
            # Send explicit event to Datadog using our new function
            try:
                # Call the bug_detection_event function
                await bug_detection_event(
                    filename=file.filename,
                    labels=amzlabels,
                    detection_type="bug",
                    additional_info=f"Bug or insect detected in image: {', '.join(amzlabels)}"
                )
                logger.info(f"Bug detection event sent to Datadog for {file.filename}")
                
                # Also send to Datadog's error events using app_event
                try:
                    await app_event(
                        event_type="error",
                        message=f"Bug detected in image: {file.filename}. Labels: {', '.join(amzlabels)}"
                    )
                    logger.info(f"Bug error event sent to Datadog via app_event for {file.filename}")
                except Exception as app_event_error:
                    logger.error(f"Failed to send bug error via app_event to Datadog: {app_event_error}")
                
                # For demo purposes: generate an unhandled error with stack trace
                generate_unhandled_error(
                    f"Bug detected in image: {file.filename}",
                    amzlabels
                )
                logger.info(f"Generated demo unhandled error for {file.filename}")
                
            except Exception as event_error:
                logger.error(f"Failed to send bug detection event to Datadog: {event_error}")
            
            bug_detected_triggered = True
            response_data["warning"] = error_message
            response_data["type"] = "bug_detected"
            response_data["labels"] = amzlabels
    except Exception as e:
        # Log the error to Datadog but don't return an error response
        logger.error(f"Bug detection check error: {str(e)}")

    # If any issues were detected, add a flag to the response
    if moderation_triggered or error_text_triggered or bug_detected_triggered:
        response_data["has_issues"] = True
    
    return response_data

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
    logger.info(f"Attempt to Delete File {id} from {backend}")

    if backend == "mongo":
        # Attempt to delete the image from MongoDB
        try:
            image = await get_one_mongo(id)
            res = await delete_one_mongo(id)
        except CustomError as e:
            error_tags = [("error.source", "mongodb"), ("error.type", "delete_failure"), ("error.id", id)]
            logger.error(f"MongoDB delete error: {str(e)}")
            return {"error": str(e), "type": "mongodb_delete_error", "id": id}
    elif backend == "postgres":
        # Attempt to delete the image from Postgres
        try:
            image = await get_image_postgres(id)
            res = await delete_image_postgres(id)
        except CustomError as e:
            error_tags = [("error.source", "postgres"), ("error.type", "delete_failure"), ("error.id", id)]
            logger.error(f"PostgreSQL delete error: {str(e)}")
            return {"error": str(e), "type": "postgres_delete_error", "id": id}
    elif backend == "sqlserver":
        # Attempt to delete the image from SQL Server
        try:
            image = await get_image_sqlserver(int(id))
            res = await delete_image_sqlserver(int(id))
        except CustomError as e:
            error_tags = [("error.source", "sqlserver"), ("error.type", "delete_failure"), ("error.id", id)]
            logger.error(f"SQL Server delete error: {str(e)}")
            return {"error": str(e), "type": "sqlserver_delete_error", "id": id}
    else:
        error_tags = [
            ("error.source", "backend_selection"),
            ("error.type", "invalid_backend"),
            ("error.backend", backend)
        ]
        error = CustomError(
            message="Backend not supported",
            error_type="invalid_backend",
            tags=error_tags
        )
        logger.error(f"Backend error: {str(error)}")
        return {"error": str(error), "type": "backend_error", "backend": backend}

    # Attempt to delete the image from Amazon S3
    try:
        logger.debug(f"Image to delete: {image}")
        res = await amazon_delete_one_s3(image["name"])
        logger.debug(f"S3 deletion result: {res}")
    except CustomError as e:
        error_tags = [("error.source", "s3"), ("error.type", "delete_failure"), ("error.id", id)]
        logger.error(f"S3 delete error: {str(e)}")
        return {"error": str(e), "type": "s3_delete_error", "id": id, "filename": image.get("name", "unknown")}
    
    return {"message": f"Image {id} successfully deleted"}

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

@app.get("/health")
async def health_check():
    """
    Health check endpoint for deployment verification.
    
    Returns:
        dict: Health status and basic application info.
    """
    return {
        "status": "healthy",
        "service": os.getenv('DD_SERVICE', 'fastapi-app'),
        "version": os.getenv('DD_VERSION', '1.0'),
        "environment": os.getenv('DD_ENV', 'dev')
    }

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

# Define a custom exception for demo purposes
class DemoBugDetectionError(Exception):
    """Custom exception for demo purposes to show unhandled bugs."""
    pass

# Define a function to deliberately generate an unhandled error for demo purposes
def generate_unhandled_error(error_message, labels=None):
    """
    Generate an unhandled error for demonstration purposes.
    This will create a stack trace in Datadog but won't crash the application.
    
    Args:
        error_message: The error message to include
        labels: Additional context for the error
    """
    # Get Datadog service information from environment variables
    dd_service = os.getenv('DD_SERVICE', 'fastapi-app')
    dd_env = os.getenv('DD_ENV', 'dev')
    dd_version = os.getenv('DD_VERSION', '1.0')
    
    # Create a child span that will contain the error
    with tracer.trace("demo.unhandled_error") as span:
        # Add service information
        span.set_tag("service", dd_service)
        span.set_tag("env", dd_env)
        span.set_tag("version", dd_version)
        
        # Add error information
        span.set_tag("error.type", "demo_unhandled_error")
        span.set_tag("error.message", error_message)
        span.set_tag("error.demo", "true")
        span.set_tag("error.category", "bug_detection")
        
        if labels:
            span.set_tag("error.labels", str(labels))
        
        try:
            # Create a nested stack to make the trace more interesting
            def nested_function_1():
                def nested_function_2():
                    # Deliberately raise our custom exception
                    raise DemoBugDetectionError(f"DEMO UNHANDLED ERROR: {error_message}")
                nested_function_2()
            nested_function_1()
        except Exception as e:
            # Set span as error but don't handle the exception
            span.set_traceback()
            # Re-raise in the span context so it's captured but don't actually bubble it up
            try:
                raise e
            except Exception:
                # Now we're outside the re-raise, Datadog has captured it as unhandled
                # but we suppress it here so the application continues
                pass

# Add a /save-youtube-to-notion endpoint that's just a shortcut for the summarize-youtube endpoint with save_to_notion=True
@app.post("/api/v1/save-youtube-to-notion", tags=["Notion"])
async def save_youtube_to_notion(
    request: YouTubeRequest
):
    """
    Save a YouTube video summary to Notion.
    This is a convenience endpoint that sets save_to_notion=True automatically.

    - **url**: YouTube video URL (required)
    - **instructions**: Optional custom instructions for the summarization
    """
    # Force save_to_notion to be True
    modified_request = YouTubeRequest(
        url=request.url,
        instructions=request.instructions,
        save_to_notion=True
    )
    
    # Reuse the existing endpoint logic
    return await summarize_youtube_video(modified_request)
