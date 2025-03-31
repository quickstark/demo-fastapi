from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs
import os
import json
from ddtrace import tracer
import logging

# Set up logging
logger = logging.getLogger(__name__)

def process_youtube_video(youtube_url: str, instructions: str = None):
    """Process a YouTube video to get transcript and generate summary"""
    try:
        # Extract video ID
        video_id = get_video_id(youtube_url)
        if not video_id:
            logger.error(f"Invalid YouTube URL: {youtube_url}")
            return {"error": "Invalid YouTube URL"}

        # Get transcript
        transcript_result = get_youtube_transcript(video_id)
        if "error" in transcript_result:
            logger.error(f"Transcript error for video {video_id}: {transcript_result['error']}")
            return transcript_result

        # Generate summary
        summary_result = generate_video_summary(transcript_result["transcript"], instructions)
        if "error" in summary_result:
            logger.error(f"Summary error for video {video_id}: {summary_result['error']}")
            
        return {
            "video_id": video_id,
            "transcript": transcript_result["transcript"],
            "language": transcript_result["language"],
            "summary": summary_result.get("summary", None),
            "error": summary_result.get("error", None)
        }
    except Exception as e:
        logger.error(f"Unexpected error in process_youtube_video: {str(e)}")
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
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes YouTube video transcripts accurately and concisely."},
                {"role": "user", "content": prompt}
            ]
        )
        
        summary = response.choices[0].message.content
        
        return {"summary": summary}
    except Exception as e:
        logger.error(f"Error during AI summarization: {str(e)}")
        return {"error": f"Error during AI summarization: {str(e)}"} 