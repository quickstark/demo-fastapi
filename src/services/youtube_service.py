from openai import AsyncOpenAI, OpenAI
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs
import os
import json
from ddtrace import tracer
import logging
import asyncio
from datetime import datetime
from .notion_service import add_video_summary_to_notion, NotionVideoPayload
from pytube import YouTube
import httpx
import re

# Set up logging
logger = logging.getLogger(__name__)

async def process_youtube_video(youtube_url: str, instructions: str = None, save_to_notion: bool = False):
    """Process a YouTube video to get transcript, metadata, and generate summary"""
    try:
        # Extract video ID
        video_id = get_video_id(youtube_url)
        if not video_id:
            logger.error(f"Invalid YouTube URL: {youtube_url}")
            return {"error": "Invalid YouTube URL"}

        # Get video details using pytube - run in executor since pytube is synchronous
        video_details = {}
        if save_to_notion:
            loop = asyncio.get_running_loop()
            video_details = await loop.run_in_executor(
                None, lambda: get_youtube_video_details_pytube(youtube_url)
            )
            if "error" in video_details:
                logger.warning(f"Video details warning for {video_id}: {video_details['error']}")
                # We'll continue with the basic metadata that was returned

        logger.info(f"Retrieved video details: Title='{video_details.get('title', 'Unknown')}' Channel='{video_details.get('channel', 'Unknown')}'")

        # Get transcript - Run in executor since YouTubeTranscriptApi is synchronous
        loop = asyncio.get_running_loop()
        transcript_result = await loop.run_in_executor(
            None, lambda: get_youtube_transcript(video_id)
        )
        
        if "error" in transcript_result:
            logger.error(f"Transcript error for video {video_id}: {transcript_result['error']}")
            return transcript_result

        # Generate summary - use AsyncOpenAI client
        summary_result = await generate_video_summary_async(transcript_result["transcript"], instructions)
        if "error" in summary_result:
            logger.error(f"Summary error for video {video_id}: {summary_result['error']}")
            
        # Save to Notion if requested and we have a summary
        notion_result = {}
        if save_to_notion and "summary" in summary_result and summary_result["summary"]:
            try:
                # Prepare the payload for Notion
                payload_data = {
                    "url": youtube_url,
                    "title": video_details.get("title", f"YouTube Video: {video_id}"),
                    "published_date": video_details.get("published_date", datetime.now().isoformat()),
                    "summary": summary_result["summary"],
                    "channel": video_details.get("channel"),
                    "views": video_details.get("views"),
                }
                
                notion_payload = NotionVideoPayload(**payload_data)
                
                # Add to Notion with transcript as separate parameter
                notion_result = await add_video_summary_to_notion(
                    notion_payload, 
                    views_as_number=True,
                    transcript=transcript_result["transcript"]
                )
                if "error" in notion_result and notion_result["error"]:
                    logger.error(f"Failed to save to Notion: {notion_result['error']}")
            except Exception as e:
                logger.error(f"Error saving to Notion: {str(e)}", exc_info=True)
                notion_result = {"error": f"Error saving to Notion: {str(e)}"}
        
        # Build the response
        response = {
            "video_id": video_id,
            "transcript": transcript_result["transcript"],
            "language": transcript_result["language"],
            "summary": summary_result.get("summary", None),
            "error": summary_result.get("error", None)
        }
        
        # Add video details if available
        if video_details and "title" in video_details:
            response["title"] = video_details["title"]
        if video_details and "published_date" in video_details:
            response["published_date"] = video_details["published_date"]
        if video_details and "channel" in video_details:
            response["channel"] = video_details["channel"]
            
        # Add Notion result if available
        if notion_result:
            if "notion_page_id" in notion_result:
                response["notion_page_id"] = notion_result["notion_page_id"]
            if "error" in notion_result and notion_result["error"]:
                response["notion_error"] = notion_result["error"]
                
        return response
    except Exception as e:
        logger.error(f"Unexpected error in process_youtube_video: {str(e)}", exc_info=True)
        return {"error": f"Server error: {str(e)}"}

@tracer.wrap(service="youtube-service", resource="get_video_id")
def get_video_id(youtube_url: str) -> str:
    """Extracts the video ID from a YouTube URL."""
    try:
        parsed_url = urlparse(youtube_url)
        if parsed_url.netloc in ('www.youtube.com', 'youtube.com', 'm.youtube.com', 'youtu.be'):
            if parsed_url.netloc in ('youtu.be',):
                return parsed_url.path[1:]
            else:
                query_params = parse_qs(parsed_url.query)
                if 'v' in query_params:
                    return query_params['v'][0]
        return None
    except Exception as e:
        logger.error(f"Error extracting video ID: {str(e)}")
        return None

@tracer.wrap(service="youtube-service", resource="get_youtube_video_details_pytube")
def get_youtube_video_details_pytube(youtube_url: str):
    """Fetches title and published date for a YouTube video using pytube (no API key needed)"""
    try:
        logger.info(f"Starting pytube extraction for URL: {youtube_url}")
        
        # Create a YouTube object
        yt = YouTube(youtube_url)
        
        # Log details immediately after extraction
        title = yt.title if hasattr(yt, 'title') and yt.title else f"YouTube Video: {youtube_url.split('v=')[-1].split('&')[0]}"
        publish_date = yt.publish_date.isoformat() if hasattr(yt, 'publish_date') and yt.publish_date else datetime.now().isoformat()
        channel = yt.author if hasattr(yt, 'author') and yt.author else "Unknown Channel"
        views = yt.views if hasattr(yt, 'views') and yt.views else 0
        
        logger.info(f"Pytube extraction results - Title: {title}, Channel: {channel}, Views: {views}")
        
        # Extract the relevant information
        result = {
            "title": title,
            "published_date": publish_date,
            "channel": channel,
            "description": yt.description if hasattr(yt, 'description') and yt.description else "",
            "views": views
        }
        
        # Check if we actually got a proper title (not just "YouTube Video" or empty)
        if not title or title.startswith("YouTube Video:"):
            logger.info("No valid title from pytube, trying fallback method...")
            return get_youtube_metadata_fallback(youtube_url)
            
        logger.info(f"Returning video details: {result}")
        return result
    except Exception as e:
        error_msg = f"Error extracting YouTube metadata: {str(e)}"
        logger.error(error_msg, exc_info=True)
        # Try fallback method
        logger.info("Trying fallback metadata extraction method...")
        try:
            return get_youtube_metadata_fallback(youtube_url)
        except Exception as fallback_error:
            logger.error(f"Fallback metadata extraction failed: {str(fallback_error)}", exc_info=True)
            # Final fallback to the video ID in case of any errors
            video_id = youtube_url.split('v=')[-1].split('&')[0] if 'v=' in youtube_url else youtube_url.split('/')[-1].split('?')[0]
            return {
                "title": f"YouTube Video: {video_id}",
                "published_date": datetime.now().isoformat(),
                "channel": "Unknown Channel",
                "description": "",
                "views": 0,
                "error": error_msg
            }

def get_youtube_metadata_fallback(youtube_url: str):
    """Fallback method to get YouTube metadata using httpx and HTML parsing"""
    logger.info(f"Using httpx fallback method for URL: {youtube_url}")
    
    # Extract video ID from URL
    video_id = None
    parsed_url = urlparse(youtube_url)
    if parsed_url.netloc in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
        query_params = parse_qs(parsed_url.query)
        if 'v' in query_params:
            video_id = query_params['v'][0]
    elif parsed_url.netloc in ('youtu.be',):
        video_id = parsed_url.path[1:]
        
    if not video_id:
        logger.error(f"Could not extract video ID from URL: {youtube_url}")
        raise ValueError(f"Invalid YouTube URL: {youtube_url}")
    
    # Fetch the video page
    with httpx.Client(timeout=10) as client:
        response = client.get(f"https://www.youtube.com/watch?v={video_id}")
        if response.status_code != 200:
            logger.error(f"Failed to fetch YouTube page: {response.status_code}")
            raise ValueError(f"Failed to fetch YouTube page: {response.status_code}")
            
        html_content = response.text
        
    # Extract metadata from HTML using regex
    title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html_content)
    title = title_match.group(1) if title_match else f"YouTube Video: {video_id}"
    
    channel_match = re.search(r'<link itemprop="name" content="([^"]+)"', html_content)
    channel = channel_match.group(1) if channel_match else "Unknown Channel"
    
    # Try to extract view count - this is more complex as it could be in different formats
    views = 0
    
    # Method 1: Look for "viewCount" in JSON data
    view_count_match = re.search(r'"viewCount":"(\d+)"', html_content)
    if view_count_match:
        try:
            views = int(view_count_match.group(1))
            logger.info(f"Extracted view count from JSON data: {views}")
        except (ValueError, IndexError):
            pass
            
    # Method 2: Look for "view count" text
    if views == 0:
        view_patterns = [
            r'<meta itemprop="interactionCount" content="(\d+)"',
            r'"viewCount\\?":\\?"(\d+)\\?"',
            r'"viewCount":(\d+)',
        ]
        
        for pattern in view_patterns:
            matches = re.search(pattern, html_content)
            if matches:
                try:
                    views = int(matches.group(1))
                    logger.info(f"Extracted view count using pattern {pattern}: {views}")
                    break
                except (ValueError, IndexError):
                    continue
    
    # Format data
    result = {
        "title": title,
        "published_date": datetime.now().isoformat(),  # We don't have accurate date from this method
        "channel": channel,
        "description": "",  # We don't have description from this method
        "views": views
    }
    
    logger.info(f"Fallback extraction results - Title: {title}, Channel: {channel}, Views: {views}")
    return result

@tracer.wrap(service="youtube-service", resource="get_youtube_transcript")
def get_youtube_transcript(video_id: str):
    """Retrieves the transcript for a YouTube video ID."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        auto_transcript = transcript_list.find_transcript(['en', 'en-GB', 'en-US'])
        transcript_parts = auto_transcript.fetch()
        
        full_transcript = " ".join(part['text'] for part in transcript_parts)
        
        return {
            "transcript": full_transcript,
            "language": auto_transcript.language
        }
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        logger.error(f"Transcript retrieval error for {video_id}: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in transcript retrieval for {video_id}: {str(e)}")
        return {"error": f"Error retrieving transcript: {str(e)}"}

@tracer.wrap(service="youtube-service", resource="generate_video_summary_async")
async def generate_video_summary_async(transcript: str, instructions: str = None):
    """Generate a summary of the video transcript using OpenAI's async client"""
    try:
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Add tracing information
        span = tracer.current_span()
        if span:
            span.set_tag("transcript_length", len(transcript))
            span.set_tag("has_instructions", instructions is not None)
        
        # Prepare prompt based on instructions
        if instructions:
            prompt = f"""
            Here is a transcript from a YouTube video:
            
            {transcript}
            
            {instructions}
            """
        else:
            prompt = f"""
            Here is a transcript from a YouTube video:
            
            {transcript}
            
            Please provide a concise summary of the main points discussed in this video.
            Include key insights, topics covered, and any important conclusions.
            """
        
        response = await client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes YouTube video transcripts accurately and concisely."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Get the response content
        summary = response.choices[0].message.content
        
        return {"summary": summary}
    except Exception as e:
        logger.error(f"Error during AI summarization: {str(e)}", exc_info=True)
        return {"error": f"Error during AI summarization: {str(e)}"}

# Keep the synchronous version for backward compatibility
@tracer.wrap(service="youtube-service", resource="generate_video_summary")
def generate_video_summary(transcript: str, instructions: str = None):
    """Generate a summary of the video transcript using OpenAI"""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Add tracing information
        span = tracer.current_span()
        if span:
            span.set_tag("transcript_length", len(transcript))
            span.set_tag("has_instructions", instructions is not None)
        
        # Prepare prompt based on instructions
        if instructions:
            prompt = f"""
            Here is a transcript from a YouTube video:
            
            {transcript}
            
            {instructions}
            """
        else:
            prompt = f"""
            Here is a transcript from a YouTube video:
            
            {transcript}
            
            Please provide a concise summary of the main points discussed in this video.
            Include key insights, topics covered, and any important conclusions.
            """
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes YouTube video transcripts accurately and concisely."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Get the response content
        summary = response.choices[0].message.content
        
        return {"summary": summary}
    except Exception as e:
        logger.error(f"Error during AI summarization: {str(e)}")
        return {"error": f"Error during AI summarization: {str(e)}"} 