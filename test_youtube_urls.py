#!/usr/bin/env python3
"""
Test script to debug YouTube URL processing and transcript retrieval.
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.youtube_service import get_video_id, get_youtube_transcript

def test_video_id_extraction():
    """Test video ID extraction from different URL formats."""
    print("=== Testing Video ID Extraction ===")
    
    test_urls = [
        "https://youtu.be/YjpBqZnJkic?si=uCeBpKnXlpmt_OTP",
        "https://youtu.be/7k0UotRheN4?si=ZPpPCYsuGA4alIQv",
        "https://www.youtube.com/watch?v=YjpBqZnJkic",
        "https://www.youtube.com/watch?v=7k0UotRheN4",
        "https://youtube.com/watch?v=YjpBqZnJkic&feature=share",
    ]
    
    for url in test_urls:
        video_id = get_video_id(url)
        print(f"URL: {url}")
        print(f"Extracted Video ID: {video_id}")
        print(f"Expected: {'YjpBqZnJkic' if 'YjpBqZnJkic' in url else '7k0UotRheN4' if '7k0UotRheN4' in url else 'N/A'}")
        print("-" * 80)

def test_transcript_retrieval():
    """Test transcript retrieval for specific video IDs."""
    print("\n=== Testing Transcript Retrieval ===")
    
    test_video_ids = [
        "YjpBqZnJkic",  # From your first URL
        "7k0UotRheN4",  # From your second URL 
    ]
    
    for video_id in test_video_ids:
        print(f"\nTesting transcript retrieval for: {video_id}")
        result = get_youtube_transcript(video_id)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            transcript_preview = result['transcript'][:200] + "..." if len(result['transcript']) > 200 else result['transcript']
            print(f"✅ Success!")
            print(f"Language: {result['language']}")
            print(f"Transcript length: {len(result['transcript'])} characters")
            print(f"Preview: {transcript_preview}")
        print("-" * 80)

async def test_full_processing():
    """Test full video processing pipeline."""
    print("\n=== Testing Full Processing Pipeline ===")
    
    from services.youtube_service import process_youtube_video
    
    test_urls = [
        "https://youtu.be/YjpBqZnJkic?si=uCeBpKnXlpmt_OTP",
        "https://youtu.be/7k0UotRheN4?si=ZPpPCYsuGA4alIQv"
    ]
    
    for url in test_urls:
        print(f"\nTesting full processing for: {url}")
        try:
            result = await process_youtube_video(
                youtube_url=url,
                instructions="Provide a brief summary of the main points.",
                save_to_notion=False
            )
            
            if "error" in result and result["error"]:
                print(f"❌ Processing failed: {result['error']}")
            else:
                print(f"✅ Processing successful!")
                print(f"Video ID: {result.get('video_id', 'N/A')}")
                print(f"Title: {result.get('title', 'N/A')}")
                print(f"Language: {result.get('language', 'N/A')}")
                if result.get('summary'):
                    summary_preview = result['summary'][:200] + "..." if len(result['summary']) > 200 else result['summary']
                    print(f"Summary: {summary_preview}")
                
        except Exception as e:
            print(f"❌ Exception during processing: {str(e)}")
        
        print("-" * 80)

def main():
    """Run all tests."""
    print("YouTube URL Processing Test Suite")
    print("=" * 80)
    
    # Test 1: Video ID extraction
    test_video_id_extraction()
    
    # Test 2: Transcript retrieval
    test_transcript_retrieval()
    
    # Test 3: Full processing (async)
    print("\n" + "=" * 80)
    print("Running full processing test...")
    asyncio.run(test_full_processing())
    
    print("\n" + "=" * 80)
    print("Testing completed!")
    print("\nIf transcript retrieval still fails, this may indicate:")
    print("1. Region restrictions on the videos")
    print("2. Videos have transcripts disabled by the creator")
    print("3. Temporary YouTube API issues")
    print("4. Network connectivity issues")
    print("\nConsider using alternative transcript extraction methods if needed.")

if __name__ == "__main__":
    main()

