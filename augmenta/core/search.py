from brave import AsyncBrave
from typing import List
import asyncio
import time

# Constants
MIN_REQUEST_INTERVAL = 1.0  # Minimum time between requests in seconds
DEFAULT_RESULTS_COUNT = 5
SUPPORTED_ENGINES = {"brave"}

# Create a semaphore to control concurrent access
_search_semaphore = asyncio.Semaphore(1)
_last_request_time: float = 0.0

async def search_web(
    query: str,
    results: int = DEFAULT_RESULTS_COUNT,
    engine: str = "brave"
) -> List[str]:
    """
    Search the web for a query with rate limiting (1 request/second).
    
    Args:
        query: Search query string.
        results: Number of results to return (default: 5).
        engine: Search engine to use (currently only "brave" supported).

    Returns:
        List of valid URLs from the search results.

    Raises:
        ValueError: If engine is not supported or if results count is invalid.
        RuntimeError: If search fails.
    """
    if not query.strip():
        raise ValueError("Search query cannot be empty")
    
    if results < 1:
        raise ValueError("Results count must be positive")
        
    if engine not in SUPPORTED_ENGINES:
        raise ValueError(f"Unsupported search engine. Supported engines: {SUPPORTED_ENGINES}")

    try:
        async with _search_semaphore:
            await _enforce_rate_limit()
            
            brave = AsyncBrave()
            search_results = await brave.search(q=query, count=results)
            
            if not search_results or not search_results.web_results:
                return []
                
            return [str(item['url']) for item in search_results.web_results]
            
    except Exception as e:
        raise RuntimeError(f"Search failed: {str(e)}") from e

async def _enforce_rate_limit() -> None:
    """Enforce minimum time interval between requests."""
    global _last_request_time
    
    current_time = time.time()
    time_since_last_request = current_time - _last_request_time
    
    if time_since_last_request < MIN_REQUEST_INTERVAL:
        await asyncio.sleep(MIN_REQUEST_INTERVAL - time_since_last_request)
    
    _last_request_time = time.time()