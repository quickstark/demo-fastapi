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
    """OpenAI Fetch Account Info

    Returns:
        Dict: Account Information
    """
    return {"message": "You've reached the OpenAI endpoint"}

@router_openai.get("/openai-gen-image/{search}")
@tracer.wrap(service="openai-service", resource="generate_image")
async def openai_gen_image(search: str): 
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
    url: str
    instructions: Optional[str] = None
    save_to_notion: Optional[bool] = False

@router_openai.post("/summarize-youtube")
@tracer.wrap(service="openai-service", resource="summarize_youtube")
async def summarize_youtube_video(request: YouTubeRequest):
    """
    Process a YouTube video to get transcript and generate an AI summary using OpenAI.
    Optionally save the video details and summary to Notion.
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