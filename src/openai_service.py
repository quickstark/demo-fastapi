"""
OpenAI API functions
"""

import os
import logging
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ddtrace import tracer

from openai import OpenAI
from .services.youtube_service import get_video_id, get_youtube_transcript, generate_video_summary, process_youtube_video

# Set up logging
logger = logging.getLogger(__name__)

# Load dotenv in the base root refers to application_top
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

OPENAI = os.getenv('OPENAI_API_KEY')
if not OPENAI:
    logger.warning("OPENAI_API_KEY environment variable not set!")
else:
    logger.info("OpenAI API key found.")

client = OpenAI(
    api_key=OPENAI
)

# Create a new router for OpenAI Routes
router_openai = APIRouter()

@router_openai.get("/openai-hello")
async def openai_hello():
    """Health check endpoint for OpenAI service.
    
    Simple endpoint to verify the OpenAI service is responding and
    available for processing requests.

    Returns:
        dict: Service status message confirming OpenAI endpoint is accessible.
    """
    return {"message": "You've reached the OpenAI endpoint"}

@router_openai.get("/openai-gen-image/{search}")
@tracer.wrap(service="openai-service", resource="generate_image")
async def openai_gen_image(search: str):
    """Generate an image using OpenAI's DALL-E 3 model.
    
    Creates a 1024x1024 image based on the provided text prompt using
    OpenAI's DALL-E 3 image generation model.

    Args:
        search (str): The text prompt describing the image to generate.

    Returns:
        str: URL of the generated image.
        
    Raises:
        HTTPException: If image generation fails or API is unavailable.
    """ 
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=search,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        return image_url
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")

class YouTubeRequest(BaseModel):
    """Request model for YouTube video processing.
    
    Attributes:
        url (str): YouTube video URL to process.
        instructions (Optional[str]): Custom instructions for AI summarization.
        save_to_notion (Optional[bool]): Whether to save results to Notion database.
    """
    url: str
    instructions: Optional[str] = None
    save_to_notion: Optional[bool] = False

@router_openai.post("/summarize-youtube")
@tracer.wrap(service="openai-service", resource="summarize_youtube")
async def summarize_youtube_video(request: YouTubeRequest):
    """Process YouTube video to generate AI-powered summary.
    
    Downloads the video transcript, generates an intelligent summary using OpenAI,
    and optionally saves the results to Notion database for future reference.

    Args:
        request (YouTubeRequest): Contains YouTube URL, custom instructions, 
                                 and Notion save preference.

    Returns:
        dict: Contains video metadata, transcript, and AI-generated summary.
              Includes Notion page ID if saved to database.
        
    Raises:
        HTTPException: If video processing fails, transcript unavailable,
                      or AI summarization encounters errors.
    """
    try:
        # Process video and get result - now async
        result = await process_youtube_video(
            request.url, 
            request.instructions,
            save_to_notion=request.save_to_notion
        )
        
        # Check for errors
        if "error" in result and result["error"]:
            logger.error(f"YouTube processing error: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Build response dict with required fields
        response_dict: Dict[str, Any] = {
            "video_id": result["video_id"],
            "transcript": result["transcript"],
            "language": result["language"],
            "summary": result["summary"]
        }
        
        # Add optional fields if they exist in the result
        for field in ["title", "published_date", "notion_page_id"]:
            if field in result:
                response_dict[field] = result[field]
        
        # Add notion error if it exists but the request was successful overall
        if "notion_error" in result:
            response_dict["notion_error"] = result["notion_error"]
            
        return response_dict
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the full exception for debugging
        logger.error(f"Unexpected error in summarize_youtube_video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}") 