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

#Logger Info
logger.info(f"Set LLM Observability app name: {os.environ['DD_LLMOBS_ML_APP']}")
logger.info(f"Set LLM Observability evaluators: {os.environ['DD_LLMOBS_EVALUATORS']}")

# Load environment variables
from dotenv import load_dotenv
APP_ROOT = os.path.join(os.path.dirname(__file__))
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)
logger.info("Environment variables loaded from .env")

# Load version from VERSION file
def get_version():
    """Read version from VERSION file, fallback to environment variable or default."""
    try:
        version_file = os.path.join(APP_ROOT, 'VERSION')
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                version = f.read().strip()
                logger.info(f"Loaded version from VERSION file: {version}")
                return version
    except Exception as e:
        logger.warning(f"Could not read VERSION file: {e}")

    # Fallback to environment variable or default
    version = os.getenv('DD_VERSION', '1.0.0')
    logger.info(f"Using version from environment or default: {version}")
    return version

# Set the application version
APP_VERSION = get_version()
# Override DD_VERSION environment variable if not set
if 'DD_VERSION' not in os.environ:
    os.environ['DD_VERSION'] = APP_VERSION
    logger.info(f"Set DD_VERSION environment variable to: {APP_VERSION}")

# Define CustomError class for application-specific exceptions
# Note: This is defined before provider initialization, so it uses a deferred approach
class CustomError(Exception):
    """Custom exception class for application-specific errors."""

    def __init__(self, message, error_type=None, tags=None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type or "application_error"
        self.tags = tags or []

        # Record the error using the observability provider
        # Provider will be initialized later, so we use a deferred approach
        try:
            # Import at runtime to avoid circular dependency
            from src.observability import get_provider

            provider = get_provider()
            if provider.is_enabled:
                # Convert tags list to dict format
                tags_dict = {}
                if self.tags:
                    for tag in self.tags:
                        if isinstance(tag, tuple) and len(tag) == 2:
                            tags_dict[tag[0]] = tag[1]
                        elif isinstance(tag, str):
                            tags_dict[tag] = True

                # Record error with provider
                provider.record_error(
                    exception=self,
                    error_type=self.error_type,
                    tags=tags_dict
                )
                logger.error(f"CustomError Recorded: {message}")
            else:
                logger.error(f"CustomError (observability disabled): {message}")
        except Exception as e:
            # Fallback to basic logging if provider fails
            logger.error(f"Failed to record CustomError: {e}")
            logger.error(f"Original error: {message}")

# Import all modules that need to be instrumented BEFORE provider initialization
import httpx
import boto3
import pymongo
import psycopg
import openai  # Important for LLM observability

# Initialize observability provider (replaces direct Datadog initialization)
from src.observability import get_provider

logger.info("Initializing observability provider...")
observability_provider = get_provider()
observability_provider.initialize()
logger.info(f"Observability provider initialized: {observability_provider.name} (enabled: {observability_provider.is_enabled})")

# For backward compatibility, create tracer reference if using Datadog
# This allows existing @tracer.wrap() decorators to continue working
try:
    if observability_provider.name == "datadog" and observability_provider.is_enabled:
        from ddtrace import tracer
        logger.info("Datadog tracer reference available for backward compatibility")
    else:
        # Create a mock tracer object for non-Datadog providers
        class MockTracer:
            @staticmethod
            def wrap(**kwargs):
                def decorator(func):
                    return func
                return decorator

            @staticmethod
            def trace(name, **kwargs):
                from contextlib import contextmanager
                @contextmanager
                def noop_context():
                    yield None
                return noop_context()

            @staticmethod
            def current_span():
                return None

        tracer = MockTracer()
        logger.info(f"Using mock tracer for {observability_provider.name} provider")
except Exception as e:
    logger.warning(f"Failed to set up tracer compatibility layer: {e}")

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
from src.database_status import router as router_database_status  # Database status endpoints

# Define CORS origins
origins = [
    "http://localhost:5173",  # Vite's default port
    "http://localhost:3000",  # Just in case you're using a different port
    "http://localhost:5174",  # Local development
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://192.168.1.100:3000",
    "http://192.168.1.100:5173",
    "http://192.168.1.200:3000",
    "http://192.168.1.200:5173",
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
    app.include_router(router_database_status, prefix="/api/v1", tags=["Database Status"])
    logger.info("Database status router included.")
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
            error_tags = [
                ("error.source", "rekognition"),
                ("error.type", "content_moderation"),
                ("error.moderation_labels", ", ".join(amzmoderation)),
                ("error.filename", file.filename)
            ]

            detection_text = f"Image file: {file.filename}\\nDetected labels: {', '.join(amzmoderation)}"
            additional_info = f"Content moderation triggered for image: {', '.join(amzmoderation)}"

            try:
                success, target = await _dispatch_detection_event(
                    detection_type="moderation",
                    filename=file.filename,
                    labels=amzmoderation,
                    title=f"Content Moderation Triggered in Image: {file.filename}",
                    text=detection_text,
                    alert_type="warning",
                    additional_info=additional_info,
                    tag_prefix="moderation",
                    app_event_message=f"Content moderation triggered for image: {file.filename}. Content: {', '.join(amzmoderation)}"
                )
                if success:
                    logger.info(f"Content moderation event sent to {target} for {file.filename}")
                else:
                    logger.info(f"Content moderation event skipped (provider: {target}) for {file.filename}")
            except Exception as event_error:
                logger.error(f"Failed to send content moderation event: {event_error}")

            moderation_triggered = True
            response_data["warning"] = error_message
            response_data["type"] = "moderation_triggered"
            response_data["moderation_labels"] = amzmoderation
    except Exception as e:
        logger.error(f"Content moderation check error: {str(e)}")

    # Check if the image contained the word "error" and issue an error
    try:
        if amazon_error_text(amztext):
            error_message = f"Image Text Error - {' '.join(amztext)}"
            error_tags = [
                ("error.source", "rekognition"),
                ("error.type", "error_text_detection"),
                ("error.text", ", ".join(amztext)),
                ("error.filename", file.filename)
            ]

            detection_text = f"Image file: {file.filename}\\nDetected text: {', '.join(amztext)}"
            additional_info = f"Error text detected in image: {', '.join(amztext)}"

            try:
                success, target = await _dispatch_detection_event(
                    detection_type="error_text",
                    filename=file.filename,
                    labels=amztext,
                    title=f"Error Text Detected in Image: {file.filename}",
                    text=detection_text,
                    alert_type="error",
                    additional_info=additional_info,
                    tag_prefix="error_text",
                    app_event_message=f"Error text detected in image: {file.filename}. Text: {', '.join(amztext)}"
                )
                if success:
                    logger.info(f"Error text detection event sent to {target} for {file.filename}")
                else:
                    logger.info(f"Error text detection event skipped (provider: {target}) for {file.filename}")
            except Exception as event_error:
                logger.error(f"Failed to send error text detection event: {event_error}")

            error_text_triggered = True
            response_data["warning"] = error_message
            response_data["type"] = "error_text_detected"
            response_data["text"] = amztext
    except Exception as e:
        logger.error(f"Text error detection check error: {str(e)}")

    # Check if the image labels contained the word "bug" or "insect" and issue an error
    try:
        if amazon_error_label(amzlabels):
            error_message = f"Image Label Error - {' '.join(amzlabels)}"
            error_tags = [
                ("error.source", "rekognition"),
                ("error.type", "bug_detection"),
                ("error.labels", ", ".join(amzlabels)),
                ("error.filename", file.filename)
            ]

            detection_text = f"Image file: {file.filename}\\nDetected labels: {', '.join(amzlabels)}"
            additional_info = f"Bug or insect detected in image: {', '.join(amzlabels)}"

            try:
                success, target = await _dispatch_detection_event(
                    detection_type="bug",
                    filename=file.filename,
                    labels=amzlabels,
                    title=f"Bug Detected in Image: {file.filename}",
                    text=detection_text,
                    alert_type="error",
                    additional_info=additional_info,
                    tag_prefix="bug",
                    app_event_message=f"Bug detected in image: {file.filename}. Labels: {', '.join(amzlabels)}"
                )
                if success:
                    logger.info(f"Bug detection event sent to {target} for {file.filename}")
                else:
                    logger.info(f"Bug detection event skipped (provider: {target}) for {file.filename}")
            except Exception as event_error:
                logger.error(f"Failed to send bug detection event: {event_error}")
            finally:
                generate_unhandled_error(
                    f"Bug detected in image: {file.filename}",
                    labels=amzlabels,
                    filename=file.filename
                )
                logger.info(f"Generated demo unhandled error for {file.filename}")

            bug_detected_triggered = True
            response_data["warning"] = error_message
            response_data["type"] = "bug_detected"
            response_data["labels"] = amzlabels
    except Exception as e:
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
        "version": APP_VERSION,
        "environment": os.getenv('DD_ENV', 'dev'),
        "observability_provider": observability_provider.name,
        "observability_enabled": observability_provider.is_enabled
    }


@app.get("/test-sqlserver")
async def test_sqlserver_debug():
    """
    Test SQL Server connection and operations for debugging.
    
    Returns:
        dict: Detailed test results for SQL Server connectivity and operations.
    """
    logger.info("Starting SQL Server debug test")
    try:
        test_results = await test_sqlserver_connection()
        logger.info(f"SQL Server debug test completed: {test_results}")
        return {
            "test_type": "sqlserver_debug",
            "timestamp": "2025-01-11T00:00:00Z",
            "results": test_results
        }
    except Exception as e:
        logger.error(f"SQL Server debug test failed: {str(e)}", exc_info=True)
        return {
            "test_type": "sqlserver_debug",
            "timestamp": "2025-01-11T00:00:00Z",
            "error": str(e),
            "results": {"connection": False, "errors": [str(e)]}
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

def generate_unhandled_error(error_message, labels=None, filename=None):
    """
    Generate a synthetic error so the selected observability provider records it.

    Args:
        error_message: Message to include with the generated error
        labels: Optional list of labels/text detected in the image
        filename: Optional filename for additional context
    """
    service = os.getenv('DD_SERVICE', 'fastapi-app')
    env_name = os.getenv('DD_ENV', 'dev')
    version = os.getenv('DD_VERSION', '1.0')

    tags = {
        "service": service,
        "env": env_name,
        "version": version,
        "error.type": "demo_unhandled_error",
        "error.message": error_message,
        "error.demo": "true",
        "error.category": "bug_detection",
    }
    if labels:
        tags["error.labels"] = ", ".join(str(label) for label in labels)
    if filename:
        tags["error.filename"] = filename

    context = {
        "labels": labels or [],
        "filename": filename,
    }

    try:
        with observability_provider.trace_context("demo.unhandled_error", op="bug_detection") as span:
            _set_span_tags(span, tags)

            def nested_function_1():
                def nested_function_2():
                    raise DemoBugDetectionError(f"DEMO UNHANDLED ERROR: {error_message}")
                nested_function_2()

            try:
                nested_function_1()
            except Exception as exc:
                _mark_span_traceback(span)
                try:
                    observability_provider.record_error(
                        exception=exc,
                        error_type="demo_unhandled_error",
                        tags=tags,
                        context=context
                    )
                except Exception as record_error_exc:
                    logger.error(f"Failed to record demo unhandled error: {record_error_exc}")
    except Exception as outer_error:
        logger.error(f"Failed to generate demo unhandled error: {outer_error}")


async def _dispatch_detection_event(
    *,
    detection_type,
    filename,
    labels,
    title,
    text,
    alert_type,
    additional_info=None,
    tag_prefix=None,
    app_event_message=None,
):
    """Send detection events to the active observability provider."""
    label_values = labels or []
    combined_text = text
    if additional_info and additional_info not in text:
        combined_text = f"{text}\n\n{additional_info}"

    provider_name = observability_provider.name

    if provider_name == "datadog":
        await bug_detection_event(
            filename=filename,
            labels=label_values,
            detection_type=detection_type,
            additional_info=additional_info
        )

        event_type = "error" if alert_type == "error" else "warning"
        message = app_event_message or combined_text
        try:
            await app_event(event_type=event_type, message=message)
        except Exception as app_event_error:
            logger.error(f"Failed to send {detection_type} via app_event to Datadog: {app_event_error}")

        return True, provider_name

    if not observability_provider.is_enabled:
        return False, provider_name

    tags = _build_detection_tags(
        filename=filename,
        labels=label_values,
        detection_type=detection_type,
        tag_prefix=tag_prefix
    )

    observability_provider.record_event(
        title=title,
        text=combined_text,
        alert_type=alert_type,
        tags=tags
    )

    return True, provider_name


def _build_detection_tags(*, filename, labels, detection_type, tag_prefix=None):
    service = os.getenv('DD_SERVICE', 'fastapi-app')
    env_name = os.getenv('DD_ENV', 'dev')
    version = os.getenv('DD_VERSION', '1.0')

    tags = [
        "app:fastapi",
        f"event_type:{detection_type}",
        f"filename:{filename}",
        "source:amazon_rekognition",
        f"service:{service}",
        f"env:{env_name}",
        f"version:{version}"
    ]

    prefix = tag_prefix or detection_type
    for label in labels:
        safe_label = str(label).lower().replace(' ', '_')
        tags.append(f"{prefix}_label:{safe_label}")

    return tags


def _set_span_tags(span, tags):
    if not span or not tags:
        return

    setter = getattr(span, "set_tag", None)
    if callable(setter):
        for key, value in tags.items():
            try:
                setter(str(key), str(value))
            except Exception:
                pass
        return

    data_setter = getattr(span, "set_data", None)
    if callable(data_setter):
        for key, value in tags.items():
            try:
                data_setter(str(key), str(value))
            except Exception:
                pass


def _mark_span_traceback(span):
    if not span:
        return

    span_traceback = getattr(span, "set_traceback", None)
    if callable(span_traceback):
        try:
            span_traceback()
        except Exception:
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
