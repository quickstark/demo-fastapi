"""
Datadog Events API functions
"""

import os
import logging
from typing import Optional, List
import httpx
import time
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Path
from dotenv import load_dotenv
from ddtrace import tracer
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Set up logging
logger = logging.getLogger(__name__)

# Load dotenv in the base root refers to application_top
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

# Get Datadog API credentials
DD_API_KEY = os.getenv('DATADOG_API_KEY')
DD_APP_KEY = os.getenv('DATADOG_APP_KEY')

# Get SendGrid API key and email addresses
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
BUG_REPORT_EMAIL = os.getenv('BUG_REPORT_EMAIL', 'event-8l2d0xg2@dtdg.co')
SENDER_EMAIL = "dirk@quickstark.com"

# Get Datadog service information from environment variables or use defaults
DD_SERVICE = os.getenv('DD_SERVICE', 'fastapi-app')
DD_ENV = os.getenv('DD_ENV', 'dev')
DD_VERSION = os.getenv('DD_VERSION', '1.0')

logger.info(f"Datadog service configured: {DD_SERVICE}, env: {DD_ENV}, version: {DD_VERSION}")

if not DD_API_KEY or not DD_APP_KEY:
    logger.warning("Datadog API_KEY or APP_KEY environment variables not set!")
else:
    logger.info("Datadog API_KEY and APP_KEY found.")

if not SENDGRID_API_KEY:
    logger.warning("SENDGRID_API_KEY environment variable not set!")
else:
    logger.info("SendGrid API key found.")

# Create a new router for Datadog Routes
router_datadog = APIRouter()

# Define request models using Pydantic
class DatadogEventRequest(BaseModel):
    title: str
    text: str
    alert_type: Optional[str] = Field(
        default="info", 
        description="The type of alert: error, warning, info, success"
    )
    priority: Optional[str] = Field(
        default="normal", 
        description="The priority of the event: normal or low"
    )
    tags: Optional[List[str]] = Field(
        default=None, 
        description="A list of tags to apply to the event"
    )
    source_type_name: Optional[str] = Field(
        default="python", 
        description="The source type name of the event"
    )
    aggregation_key: Optional[str] = Field(
        default=None, 
        description="An arbitrary string to use for aggregation"
    )
    
    def __init__(self, **data):
        super().__init__(**data)
        
        # Ensure tags is initialized
        if self.tags is None:
            self.tags = []
            
        # Add universal service tags if not already present
        service_tag = f"service:{DD_SERVICE}"
        env_tag = f"env:{DD_ENV}"
        version_tag = f"version:{DD_VERSION}"
        
        if service_tag not in self.tags:
            self.tags.append(service_tag)
        if env_tag not in self.tags:
            self.tags.append(env_tag)
        if version_tag not in self.tags:
            self.tags.append(version_tag)

async def send_email_notification(subject: str, body: str, recipient: str = BUG_REPORT_EMAIL, 
                                 tags: Optional[List[str]] = None) -> bool:
    """
    Send an email notification about an event using SendGrid
    
    Args:
        subject: Email subject line
        body: Email body text
        recipient: Email recipient (defaults to BUG_REPORT_EMAIL)
        tags: List of tags to include in the email message
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not SENDGRID_API_KEY:
        logger.error("SendGrid API key not set, cannot send email")
        return False
    
    try:
        # Format subject with Datadog event format - include service name with # in title
        # Format: [<SOURCE_TYPE>] <EVENT_TITLE> #service:<SERVICE_NAME>
        formatted_subject = subject
        
        # Start with the original body content
        formatted_body = body
        
        # Add a tag section at the end of the message body
        if tags and len(tags) > 0:
            formatted_body = formatted_body.replace("\n--\n", "")  # Remove existing separator if present
            
            # Add tags in Datadog's format (with # prefix) at the end of the body
            formatted_body += "\n\n"
            
            # Always include service tag in body
            formatted_body += f"#service:{DD_SERVICE} "
            
            # Add all other tags
            for tag in tags:
                if ":" in tag and not tag.startswith(f"service:{DD_SERVICE}"):  # Avoid duplicate service tags
                    formatted_body += f"#{tag} "
            
            # Add the footer after tags
            formatted_body += "\n\n--\n"
            formatted_body += f"This is an automated notification from the FastAPI Image Service.\n"
            formatted_body += f"Environment: {DD_ENV}\n"
            formatted_body += f"Service: {DD_SERVICE}\n"
            formatted_body += f"Version: {DD_VERSION}\n"
        
        # Create a SendGrid message
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=recipient,
            subject=formatted_subject,
            plain_text_content=formatted_body
        )
        
        # Send the email using SendGrid API
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        # Log the response
        status_code = response.status_code
        if status_code >= 200 and status_code < 300:
            logger.info(f"Email notification sent to {recipient} (SendGrid status: {status_code})")
            return True
        else:
            logger.error(f"SendGrid returned non-successful status code: {status_code}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send email notification via SendGrid: {str(e)}")
        return False

@router_datadog.get("/datadog-hello")
async def datadog_hello():
    """Datadog endpoint health check

    Returns:
        Dict: Status message
    """
    return {"message": "You've reached the Datadog Events endpoint"}

@router_datadog.post("/datadog-event")
@tracer.wrap(service="datadog-service", resource="post_event")
async def post_datadog_event(request: DatadogEventRequest):
    """
    Post an event to Datadog Events API
    
    Args:
        request: Event details including title, text, alert_type, etc.
        
    Returns:
        Dict: Response from Datadog Events API
    """
    try:
        # Build the request payload
        payload = {
            "title": request.title,
            "text": request.text,
            "alert_type": request.alert_type,
            "priority": request.priority,
            "source_type_name": request.source_type_name
        }
        
        # Add optional fields if provided
        if request.tags:
            payload["tags"] = request.tags
        if request.aggregation_key:
            payload["aggregation_key"] = request.aggregation_key
            
        # Set up API endpoint and parameters
        url = "https://api.datadoghq.com/api/v1/events"
        params = {
            "api_key": DD_API_KEY,
            "application_key": DD_APP_KEY
        }
        
        # Make the API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                json=payload,
                params=params
            )
            
            # Handle response
            if response.status_code == 202:
                return response.json()
            else:
                logger.error(f"Datadog API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Datadog API error: {response.text}"
                )
    
    except httpx.RequestError as e:
        logger.error(f"Error sending event to Datadog: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending event to Datadog: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in post_datadog_event: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@router_datadog.get("/datadog-events")
@tracer.wrap(service="datadog-service", resource="get_events")
async def get_datadog_events(
    start: Optional[int] = None,
    end: Optional[int] = None,
    priority: Optional[str] = None,
    sources: Optional[str] = None,
    tags: Optional[str] = None
):
    """
    Get events from Datadog Events API with optional filtering
    
    Args:
        start: POSIX timestamp for start of query window
        end: POSIX timestamp for end of query window
        priority: Priority to filter by
        sources: Sources to filter by
        tags: Tags to filter by (comma-separated)
        
    Returns:
        Dict: List of events from Datadog Events API
    """
    try:
        # Set up API endpoint
        url = "https://api.datadoghq.com/api/v1/events"
        
        # Set up parameters
        params = {
            "api_key": DD_API_KEY,
            "application_key": DD_APP_KEY
        }
        
        # Add optional filtering parameters
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if priority:
            params["priority"] = priority
        if sources:
            params["sources"] = sources
        if tags:
            params["tags"] = tags
            
        # Make the API request
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            
            # Handle response
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Datadog API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Datadog API error: {response.text}"
                )
    
    except httpx.RequestError as e:
        logger.error(f"Error getting events from Datadog: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting events from Datadog: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in get_datadog_events: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@router_datadog.post("/app-event/{event_type}")
@tracer.wrap(service="datadog-service", resource="app_event")
async def app_event(
    event_type: str = Path(..., description="Type of event: error, warning, info, success"),
    message: str = None
):
    """
    Convenient method to post application events to Datadog
    
    Args:
        event_type: The type of event (error, warning, info, success)
        message: Custom message for the event
        
    Returns:
        Dict: Response from Datadog Events API
    """
    try:
        # Map event_type to alert_type
        if event_type not in ["error", "warning", "info", "success"]:
            event_type = "info"
            
        # Create default message if none provided
        if not message:
            message = f"Application {event_type} event triggered"
            
        # Create event payload with universal service tags
        event_request = DatadogEventRequest(
            title=f"FastAPI Application {event_type.capitalize()} Event",
            text=message,
            alert_type=event_type,
            tags=[
                "app:fastapi", 
                f"event_type:{event_type}", 
                f"service:{DD_SERVICE}", 
                f"env:{DD_ENV}", 
                f"version:{DD_VERSION}"
            ],
            source_type_name="python"
        )
        
        # Forward to the main event posting function
        return await post_datadog_event(event_request)
        
    except Exception as e:
        logger.error(f"Error posting app event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error posting app event: {str(e)}")

@router_datadog.post("/track-api-request")
@tracer.wrap(service="datadog-service", resource="track_api_request")
async def track_api_request(
    endpoint: str,
    method: str = "GET",
    status_code: int = 200,
    response_time: Optional[float] = None,
    user_id: Optional[str] = None
):
    """
    Track API requests by posting events to Datadog
    
    Args:
        endpoint: The API endpoint that was called
        method: HTTP method used (GET, POST, etc.)
        status_code: HTTP status code of the response
        response_time: Time taken to respond in milliseconds
        user_id: ID of the user who made the request
        
    Returns:
        Dict: Response from Datadog Events API
    """
    try:
        # Determine alert type based on status code
        if status_code >= 500:
            alert_type = "error"
        elif status_code >= 400:
            alert_type = "warning"
        else:
            alert_type = "info"
            
        # Create tags list with universal service tags
        tags = [
            "app:fastapi",
            f"endpoint:{endpoint}",
            f"method:{method}",
            f"status_code:{status_code}",
            f"service:{DD_SERVICE}",
            f"env:{DD_ENV}",
            f"version:{DD_VERSION}"
        ]
        
        # Add user_id tag if provided
        if user_id:
            tags.append(f"user_id:{user_id}")
            
        # Create response time text if provided
        response_time_text = ""
        if response_time:
            response_time_text = f"\nResponse time: {response_time}ms"
            
        # Create event request
        event_request = DatadogEventRequest(
            title=f"API Request: {method} {endpoint}",
            text=f"Status code: {status_code}{response_time_text}",
            alert_type=alert_type,
            tags=tags,
            source_type_name="api"
        )
        
        # Forward to the main event posting function
        return await post_datadog_event(event_request)
        
    except Exception as e:
        logger.error(f"Error tracking API request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error tracking API request: {str(e)}")

@router_datadog.post("/bug-detection-event")
@tracer.wrap(service="datadog-service", resource="bug_detection_event")
async def bug_detection_event(
    filename: str,
    labels: List[str],
    detection_type: str = "bug",  # Can be "bug", "error_text", "moderation"
    additional_info: Optional[str] = None
):
    """
    Send a bug detection event to Datadog and email notification
    
    Args:
        filename: The name of the image file
        labels: List of labels detected in the image
        detection_type: Type of detection ("bug", "error_text", "moderation")
        additional_info: Any additional information about the detection
        
    Returns:
        Dict: Response from Datadog Events API
    """
    try:
        # Create title based on detection type
        if detection_type == "bug":
            title = f"Bug Detected in Image: {filename}"
            alert_type = "error"
            tag_prefix = "bug"
        elif detection_type == "error_text":
            title = f"Error Text Detected in Image: {filename}"
            alert_type = "error"
            tag_prefix = "error_text"
        elif detection_type == "moderation":
            title = f"Content Moderation Triggered in Image: {filename}"
            alert_type = "warning"
            tag_prefix = "moderation"
        else:
            title = f"Image Detection Alert: {filename}"
            alert_type = "info"
            tag_prefix = "detection"
            
        # Create text message
        text = f"Image file: {filename}\nDetected labels: {', '.join(labels)}"
        if additional_info:
            text += f"\n\nAdditional info: {additional_info}"
            
        # Create tags
        tags = [
            "app:fastapi",
            f"event_type:{detection_type}",
            f"filename:{filename}",
            "source:amazon_rekognition",
            f"service:{DD_SERVICE}",
            f"env:{DD_ENV}",
            f"version:{DD_VERSION}"
        ]
        
        # Add label tags
        for label in labels:
            safe_label = label.lower().replace(' ', '_')
            tags.append(f"{tag_prefix}_label:{safe_label}")
            
        # Create event payload
        event_request = DatadogEventRequest(
            title=title,
            text=text,
            alert_type=alert_type,
            priority="normal",
            tags=tags,
            source_type_name="amazon_rekognition"
        )
        
        # Send email notification for bug detection
        if detection_type == "bug":
            # Create a more detailed message for the email
            email_body = (
                f"Bug Detection Alert\n"
                f"==================\n\n"
                f"A potential bug has been detected in an image:\n\n"
                f"Image filename: {filename}\n"
                f"Detected labels: {', '.join(labels)}\n"
            )
            
            if additional_info:
                email_body += f"\nAdditional information:\n{additional_info}\n"
                
            # Add service tag with # to the email subject
            email_subject = f"[AMAZON_REKOGNITION] {title} #service:{DD_SERVICE}"
            
            # All other tags go in the body (service tag will be added by the send_email_notification function)
            email_tags = [
                f"env:{DD_ENV}",
                f"filename:{filename}",
                f"event_type:{detection_type}"
            ]
            
            # Send email notification with properly formatted tags
            await send_email_notification(
                subject=email_subject,
                body=email_body,
                tags=email_tags
            )
        
        # Forward to the main event posting function
        return await post_datadog_event(event_request)
        
    except Exception as e:
        logger.error(f"Error posting bug detection event: {str(e)}")
        # Try to send error email notification even if the main process failed
        try:
            error_email_body = (
                f"Bug Detection System Error\n"
                f"========================\n\n"
                f"An error occurred while processing bug detection:\n\n"
                f"Error: {str(e)}\n\n"
                f"Event details:\n"
                f"- Filename: {filename}\n"
                f"- Labels: {', '.join(labels)}\n"
                f"- Detection type: {detection_type}\n"
            )
            
            if additional_info:
                error_email_body += f"- Additional info: {additional_info}\n"
            
            # Error email tags with # in subject
            error_email_subject = f"[ERROR] Bug Detection Error: {detection_type} - {filename} #service:{DD_SERVICE}"
            
            # Error email tags for body (service tag will be added by the send_email_notification function)
            error_email_tags = [
                f"env:{DD_ENV}",
                f"filename:{filename}",
                f"event_type:error",
                f"error:true"
            ]
            
            await send_email_notification(
                subject=error_email_subject,
                body=error_email_body,
                tags=error_email_tags
            )
        except Exception as email_error:
            logger.error(f"Failed to send error notification email: {str(email_error)}")
        
        # Raise exception for API error handling
        raise HTTPException(status_code=500, detail=f"Error posting bug detection event: {str(e)}")