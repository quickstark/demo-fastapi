# YouTube Batch Processing Guide

## Overview

The YouTube Batch Processing feature allows you to process multiple YouTube videos simultaneously while managing OpenAI's context window limitations. The system provides four different processing strategies to handle various use cases.

## Context Window Management

**The Challenge:**
- OpenAI GPT-4.1-mini has ~128k token context window
- Average 10-minute YouTube video ≈ 15k-25k tokens  
- Multiple videos would easily exceed limits
- Need intelligent processing strategies

**Our Solution:**
- Multiple processing strategies with different trade-offs
- Intelligent token counting and chunking
- Parallel processing with concurrency limits
- Meta-analysis capabilities for combined insights

## Processing Strategies

### 1. Sequential (`sequential`)
- **Best for:** Maximum reliability, debugging
- **How it works:** Processes videos one by one
- **Pros:** Most reliable, easier error tracking, no concurrency issues
- **Cons:** Slowest option, no combined analysis
- **Use when:** You need guaranteed processing or are debugging issues

### 2. Parallel Individual (`parallel_individual`) - **RECOMMENDED**
- **Best for:** General use, balanced performance and reliability
- **How it works:** Processes videos in parallel, generates individual summaries
- **Pros:** Fast processing, individual summaries, good reliability
- **Cons:** No combined analysis across videos
- **Use when:** You want individual summaries for each video quickly

### 3. Batch Combined (`batch_combined`)
- **Best for:** Related videos that should be analyzed together
- **How it works:** Attempts combined analysis with intelligent chunking
- **Pros:** Single coherent analysis across all videos
- **Cons:** May fail if total content exceeds context window
- **Use when:** Videos are related and you want cross-video insights

### 4. Hybrid (`hybrid`)
- **Best for:** Comprehensive analysis with individual and combined insights
- **How it works:** Individual summaries + meta-analysis of summaries
- **Pros:** Both individual and combined analysis
- **Cons:** Slower, higher token usage
- **Use when:** You need both individual summaries and cross-video analysis

## API Endpoints

### Batch Processing Endpoint

```http
POST /api/v1/batch-summarize-youtube
```

**Request Body:**
```json
{
  "urls": [
    "https://www.youtube.com/watch?v=video1",
    "https://www.youtube.com/watch?v=video2"
  ],
  "strategy": "parallel_individual",
  "instructions": "Focus on key technical concepts",
  "save_to_notion": false,
  "max_parallel": 3
}
```

**Parameters:**
- `urls` (required): Array of YouTube video URLs (max 20)
- `strategy` (optional): Processing strategy - "sequential", "parallel_individual", "batch_combined", or "hybrid"
- `instructions` (optional): Custom instructions for AI summarization
- `save_to_notion` (optional): Whether to save results to Notion database
- `max_parallel` (optional): Maximum concurrent processing (1-10, default: 3)

**Response:**
```json
{
  "strategy_used": "parallel_individual",
  "total_videos": 3,
  "successful_videos": 2,
  "failed_videos": 1,
  "processing_time": 45.67,
  "results": [
    {
      "url": "https://www.youtube.com/watch?v=video1",
      "video_id": "video1",
      "title": "Example Video Title",
      "success": true,
      "summary": "Video summary...",
      "processing_time": 23.45,
      "notion_page_id": "page_id",
      "error": null
    }
  ],
  "meta_summary": "Combined analysis..." // Only for hybrid/batch_combined strategies
}
```

### Single Video Endpoint (Original)

```http
POST /api/v1/summarize-youtube
```

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=video_id",
  "instructions": "Custom instructions",
  "save_to_notion": false
}
```

## Usage Examples

### Python Client Example

```python
import asyncio
import httpx

async def process_videos():
    urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=oHg5SJYRHA0"
    ]
    
    payload = {
        "urls": urls,
        "strategy": "parallel_individual",
        "instructions": "Focus on practical takeaways",
        "save_to_notion": False,
        "max_parallel": 2
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            "http://localhost:8000/api/v1/batch-summarize-youtube",
            json=payload
        )
        result = response.json()
        
        print(f"Processed {result['successful_videos']} videos successfully")
        for video in result['results']:
            if video['success']:
                print(f"✅ {video['title']}: {video['summary'][:100]}...")

asyncio.run(process_videos())
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/batch-summarize-youtube" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.youtube.com/watch?v=example1",
      "https://www.youtube.com/watch?v=example2"
    ],
    "strategy": "parallel_individual",
    "instructions": "Focus on main concepts and practical applications",
    "max_parallel": 2
  }'
```

## Performance Considerations

### Processing Time Estimates

- **Single video:** 15-45 seconds (depending on length)
- **Sequential (3 videos):** 45-135 seconds
- **Parallel (3 videos, max_parallel=3):** 15-45 seconds
- **Hybrid (3 videos):** 30-90 seconds (includes meta-analysis)

### Concurrency Limits

- **Default max_parallel:** 3
- **Maximum allowed:** 10
- **Recommended:** 2-5 (balance between speed and API rate limits)

### Token Usage

- **Individual summary:** ~2k-4k tokens per video
- **Combined analysis:** Varies based on transcript length
- **Meta-summary:** Additional ~1k-2k tokens

## Error Handling

The system gracefully handles various error conditions:

- **Invalid URLs:** Marked as failed with descriptive error
- **Transcript unavailable:** Video marked as failed, others continue
- **API rate limits:** Automatic retry with exponential backoff
- **Context window exceeded:** Automatic chunking or fallback strategies
- **Network errors:** Individual video failures don't stop batch processing

## Best Practices

### Strategy Selection

1. **Start with `parallel_individual`** for most use cases
2. **Use `batch_combined`** only when videos are closely related
3. **Use `hybrid`** when you need both individual and combined insights
4. **Use `sequential`** for debugging or when reliability is critical

### URL Batching

- **Optimal batch size:** 3-5 videos
- **Maximum batch size:** 20 videos
- **Group related content** for better combined analysis
- **Mix short and long videos** to balance processing time

### Error Recovery

- Check individual video `success` status
- Retry failed videos individually if needed
- Use sequential strategy for problematic videos
- Monitor processing times and adjust `max_parallel`

### Performance Optimization

- Use appropriate `max_parallel` (2-5 recommended)
- Batch related videos together
- Use specific instructions to focus AI processing
- Monitor token usage for cost optimization

## Integration with Notion

When `save_to_notion=true`:

- Each successful video creates a Notion page
- Full transcript included as page content
- Video metadata (title, channel, views) included
- Combined summaries use individual video metadata

## Environment Variables

Required environment variables:
```bash
OPENAI_API_KEY=your_openai_api_key
NOTION_API_KEY=your_notion_api_key  # Optional, for Notion integration
NOTION_DATABASE_ID=your_database_id  # Optional, for Notion integration
```

## Limitations

- Maximum 20 URLs per batch request
- Individual video transcript length limits (~100k tokens)
- OpenAI API rate limits apply
- YouTube transcript availability varies by video
- Processing time scales with video count and length

## Troubleshooting

### Common Issues

1. **"Invalid YouTube URL" errors:** Check URL format and video availability
2. **Timeout errors:** Reduce batch size or increase client timeout
3. **Context window exceeded:** Use different strategy or shorter videos
4. **Rate limit errors:** Reduce `max_parallel` or add delays between requests

### Debug Mode

Use sequential strategy for debugging:
```json
{
  "strategy": "sequential",
  "max_parallel": 1
}
```

This provides detailed error information for each video individually.

## Future Enhancements

Planned improvements:
- Support for transcript chunking within individual videos
- Custom retry policies
- Webhook notifications for long-running batches
- Integration with more summarization models
- Advanced analytics and reporting
