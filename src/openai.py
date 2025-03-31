"""
OpenAI API functions
"""

import os
import logging
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
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

@router_openai.post("/summarize-youtube")
@tracer.wrap(service="openai-service", resource="summarize_youtube")
async def summarize_youtube_video(request: YouTubeRequest):
    """
    Process a YouTube video to get transcript and generate an AI summary using OpenAI
    """
    try:
        # Process video and get result
        result = process_youtube_video(request.url, request.instructions)
        
        # Check for errors
        if "error" in result and result["error"]:
            logger.error(f"YouTube processing error: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Return successful response
        return {
            "video_id": result["video_id"],
            "transcript": result["transcript"],
            "language": result["language"],
            "summary": result["summary"]
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the full exception for debugging
        logger.error(f"Unexpected error in summarize_youtube_video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}") 