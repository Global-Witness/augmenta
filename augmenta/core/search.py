from brave import AsyncBrave
from typing import List
import asyncio
import time
from oxylabs import AsyncClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
DEFAULT_RESULTS_COUNT = 5
SUPPORTED_ENGINES = {"brave", "oxylabs_google", "oxylabs_bing"}

# Create a semaphore to control concurrent access
_search_semaphore = asyncio.Semaphore(1)
_last_request_time: float = 0.0

# Get Oxylabs credentials from environment
OXYLABS_USERNAME = os.getenv('OXYLABS_USERNAME')
OXYLABS_PASSWORD = os.getenv('OXYLABS_PASSWORD')

async def search_web(
    query: str,
    results: int = DEFAULT_RESULTS_COUNT,
    engine: str = "brave",
    rate_limit: float = 1.0,
) -> List[str]:
    """
    Search the web for a query with rate limiting (1 request/second).
    
    Args:
        query: Search query string.
        results: Number of results to return (default: 5).
        engine: Search engine to use ("brave", "oxylabs_google", or "oxylabs_bing").
        rate_limit: Time between requests in seconds.

    Returns:
        List of valid URLs from the search results.

    Raises:
        ValueError: If engine is not supported or if results count is invalid.
        RuntimeError: If search fails or Oxylabs credentials are missing.
    """
    if not query.strip():
        raise ValueError("Search query cannot be empty")
    
    if results < 1:
        raise ValueError("Results count must be positive")
        
    if engine not in SUPPORTED_ENGINES:
        raise ValueError(f"Unsupported search engine. Supported engines: {SUPPORTED_ENGINES}")

    if engine.startswith("oxylabs_"):
        if not OXYLABS_USERNAME or not OXYLABS_PASSWORD:
            raise RuntimeError("Oxylabs credentials not found in environment variables")

    try:
        async with _search_semaphore:
            await _enforce_rate_limit(rate_limit=rate_limit)
            
            if engine == "brave":
                brave = AsyncBrave()
                search_results = await brave.search(q=query, count=results)
                
                if not search_results or not search_results.web_results:
                    return []
                    
                return [str(item['url']) for item in search_results.web_results]
            
            else:  # Oxylabs engines
                client = AsyncClient(OXYLABS_USERNAME, OXYLABS_PASSWORD)
                
                if engine == "oxylabs_google":
                    result = await client.serp.google.scrape_search(
                        query,
                        parse=True,
                        limit=results,
                        timeout=35,
                        poll_interval=3,
                    )
                else:  # oxylabs_bing
                    result = await client.serp.bing.scrape_search(
                        query,
                        parse=True,
                        limit=results,
                        timeout=35,
                        poll_interval=3,
                    )
                
                if not result or not result.results:
                    return []
                
                # Extract URLs from organic search results
                urls = []
                for item in result.results.get('organic', [])[:results]:
                    if 'url' in item:
                        urls.append(item['url'])
                return urls
            
    except Exception as e:
        raise RuntimeError(f"Search failed: {str(e)}") from e

async def _enforce_rate_limit(rate_limit: float) -> None:
    """Enforce minimum time interval between requests."""
    global _last_request_time
    
    current_time = time.time()
    time_since_last_request = current_time - _last_request_time
    
    if time_since_last_request < rate_limit:
        await asyncio.sleep(rate_limit - time_since_last_request)
    
    _last_request_time = time.time()