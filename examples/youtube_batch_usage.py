"""
YouTube Batch Processing Usage Examples

This file demonstrates how to use the new batch YouTube processing endpoint
with different strategies and configurations.
"""

import asyncio
import httpx
import json
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000/api/v1"

class YouTubeBatchClient:
    """Client for interacting with the batch YouTube processing API."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    async def process_batch(
        self,
        urls: List[str],
        strategy: str = "parallel_individual",
        instructions: str = None,
        save_to_notion: bool = False,
        max_parallel: int = 3
    ) -> Dict[str, Any]:
        """Process a batch of YouTube URLs."""
        
        payload = {
            "urls": urls,
            "strategy": strategy,
            "instructions": instructions,
            "save_to_notion": save_to_notion,
            "max_parallel": max_parallel
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
            response = await client.post(
                f"{self.base_url}/batch-summarize-youtube",
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def process_single(
        self,
        url: str,
        instructions: str = None,
        save_to_notion: bool = False
    ) -> Dict[str, Any]:
        """Process a single YouTube URL (original endpoint)."""
        
        payload = {
            "url": url,
            "instructions": instructions,
            "save_to_notion": save_to_notion
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/summarize-youtube",
                json=payload
            )
            response.raise_for_status()
            return response.json()

# Example usage scenarios
async def example_1_parallel_individual():
    """Example 1: Process multiple videos in parallel with individual summaries."""
    
    print("=== Example 1: Parallel Individual Processing ===")
    
    client = YouTubeBatchClient()
    
    # Sample YouTube URLs (replace with actual URLs)
    urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Replace with real URLs
        "https://www.youtube.com/watch?v=oHg5SJYRHA0",  # Replace with real URLs
        "https://www.youtube.com/watch?v=iik25wqIuFo"   # Replace with real URLs
    ]
    
    try:
        result = await client.process_batch(
            urls=urls,
            strategy="parallel_individual",
            instructions="Focus on the main educational points and practical takeaways.",
            save_to_notion=False,
            max_parallel=3
        )
        
        print(f"Processed {result['successful_videos']}/{result['total_videos']} videos successfully")
        print(f"Processing time: {result['processing_time']} seconds")
        
        for video_result in result['results']:
            if video_result['success']:
                print(f"\n✅ {video_result['title']}")
                print(f"Summary: {video_result['summary'][:200]}...")
            else:
                print(f"\n❌ {video_result['url']}")
                print(f"Error: {video_result['error']}")
                
    except Exception as e:
        print(f"Error: {e}")

async def example_2_batch_combined():
    """Example 2: Process videos with combined analysis."""
    
    print("\n=== Example 2: Batch Combined Analysis ===")
    
    client = YouTubeBatchClient()
    
    # URLs should be related topics for best results
    urls = [
        "https://www.youtube.com/watch?v=example1",  # Replace with real related URLs
        "https://www.youtube.com/watch?v=example2",  # Replace with real related URLs
    ]
    
    try:
        result = await client.process_batch(
            urls=urls,
            strategy="batch_combined",
            instructions="Compare and contrast the different approaches presented in these videos.",
            save_to_notion=False,
            max_parallel=2
        )
        
        print(f"Strategy used: {result['strategy_used']}")
        print(f"Processing time: {result['processing_time']} seconds")
        
        if 'meta_summary' in result:
            print(f"\n🔍 Combined Analysis:")
            print(result['meta_summary'])
        
        for video_result in result['results']:
            print(f"\n📹 {video_result['title']}: {'✅' if video_result['success'] else '❌'}")
                
    except Exception as e:
        print(f"Error: {e}")

async def example_3_hybrid_approach():
    """Example 3: Hybrid approach with individual summaries and meta-analysis."""
    
    print("\n=== Example 3: Hybrid Processing ===")
    
    client = YouTubeBatchClient()
    
    urls = [
        "https://www.youtube.com/watch?v=example1",  # Replace with real URLs
        "https://www.youtube.com/watch?v=example2",  # Replace with real URLs
        "https://www.youtube.com/watch?v=example3",  # Replace with real URLs
    ]
    
    try:
        result = await client.process_batch(
            urls=urls,
            strategy="hybrid",
            instructions="Focus on actionable insights and how they connect across videos.",
            save_to_notion=False,
            max_parallel=2
        )
        
        print(f"Processed {result['successful_videos']}/{result['total_videos']} videos")
        
        # Show individual summaries
        print("\n📝 Individual Summaries:")
        for video_result in result['results']:
            if video_result['success']:
                print(f"\n{video_result['title']}: {video_result['summary'][:150]}...")
        
        # Show meta-summary
        if 'meta_summary' in result:
            print(f"\n🎯 Meta-Analysis:")
            print(result['meta_summary'])
                
    except Exception as e:
        print(f"Error: {e}")

async def example_4_sequential_safe():
    """Example 4: Sequential processing for maximum reliability."""
    
    print("\n=== Example 4: Sequential Processing ===")
    
    client = YouTubeBatchClient()
    
    urls = [
        "https://www.youtube.com/watch?v=example1",  # Replace with real URLs
        "https://www.youtube.com/watch?v=example2",  # Replace with real URLs
    ]
    
    try:
        result = await client.process_batch(
            urls=urls,
            strategy="sequential",
            instructions="Provide detailed technical summaries with key timestamps.",
            save_to_notion=True,  # Save to Notion
            max_parallel=1  # Ignored for sequential
        )
        
        print(f"Sequential processing completed in {result['processing_time']} seconds")
        
        for i, video_result in enumerate(result['results'], 1):
            print(f"\n{i}. {video_result['title']}")
            if video_result['success']:
                print(f"   ✅ Processed in {video_result['processing_time']:.1f}s")
                if video_result['notion_page_id']:
                    print(f"   📄 Saved to Notion: {video_result['notion_page_id']}")
            else:
                print(f"   ❌ Failed: {video_result['error']}")
                
    except Exception as e:
        print(f"Error: {e}")

async def example_5_error_handling():
    """Example 5: Demonstrate error handling with mixed valid/invalid URLs."""
    
    print("\n=== Example 5: Error Handling ===")
    
    client = YouTubeBatchClient()
    
    # Mix of valid and invalid URLs
    urls = [
        "https://www.youtube.com/watch?v=valid_video_id",    # Replace with real URL
        "https://not-youtube.com/invalid",                  # Invalid URL
        "https://www.youtube.com/watch?v=another_valid_id", # Replace with real URL
        "not_a_url_at_all",                                # Invalid format
    ]
    
    try:
        result = await client.process_batch(
            urls=urls,
            strategy="parallel_individual",
            max_parallel=2
        )
        
        print(f"Results: {result['successful_videos']} success, {result['failed_videos']} failed")
        
        # Show detailed results
        for video_result in result['results']:
            status = "✅ SUCCESS" if video_result['success'] else "❌ FAILED"
            print(f"{status}: {video_result['url']}")
            if video_result['error']:
                print(f"   Error: {video_result['error']}")
                
    except Exception as e:
        print(f"Error: {e}")

async def benchmark_strategies():
    """Compare performance of different strategies."""
    
    print("\n=== Strategy Performance Benchmark ===")
    
    client = YouTubeBatchClient()
    
    # Use the same URLs for fair comparison
    test_urls = [
        "https://www.youtube.com/watch?v=example1",  # Replace with real URLs
        "https://www.youtube.com/watch?v=example2",  # Replace with real URLs
        "https://www.youtube.com/watch?v=example3",  # Replace with real URLs
    ]
    
    strategies = ["sequential", "parallel_individual", "hybrid"]
    
    for strategy in strategies:
        try:
            print(f"\n⏱️ Testing {strategy}...")
            result = await client.process_batch(
                urls=test_urls,
                strategy=strategy,
                max_parallel=3
            )
            
            print(f"   Time: {result['processing_time']:.2f}s")
            print(f"   Success: {result['successful_videos']}/{result['total_videos']}")
            
        except Exception as e:
            print(f"   Error: {e}")

# Main execution
async def main():
    """Run all examples."""
    
    print("YouTube Batch Processing Examples")
    print("=" * 50)
    
    # Run examples (comment out examples that require real URLs)
    
    # await example_1_parallel_individual()
    # await example_2_batch_combined()  
    # await example_3_hybrid_approach()
    # await example_4_sequential_safe()
    await example_5_error_handling()
    # await benchmark_strategies()
    
    print("\n" + "=" * 50)
    print("Examples completed! Replace example URLs with real YouTube URLs to test.")

if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
