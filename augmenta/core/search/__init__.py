from typing import List
from .factory import SearchProviderFactory
from .rate_limiter import RateLimiter
from .providers import SearchProvider, BraveSearchProvider, OxylabsSearchProvider

# Create a single global rate limiter instance
_rate_limiter = None

async def search_web(
    query: str,
    results: int,
    engine: str,
    rate_limit: float,
    credentials: dict
) -> List[str]:
    """
    Search the web using the specified engine with rate limiting
    
    Args:
        query: Search query string
        results: Number of results to return
        engine: Search engine to use ("brave", "oxylabs_google", or "oxylabs_bing")
        rate_limit: Time between requests in seconds
        credentials: Dictionary containing API credentials
        
    Returns:
        List of URLs from search results
        
    Raises:
        ValueError: If query is empty or results count is invalid
        RuntimeError: If search fails
    """
    if not query.strip():
        raise ValueError("Search query cannot be empty")
    
    if results < 1:
        raise ValueError("Results count must be positive")
        
    try:
        # Use global rate limiter to ensure all searches are rate limited
        global _rate_limiter
        if _rate_limiter is None:
            _rate_limiter = RateLimiter(rate_limit)
            
        provider = SearchProviderFactory.create(engine, credentials)
        
        # Rate limit at the search_web level, not the provider level
        await _rate_limiter.acquire()
        return await provider.search(query, results)
        
    except Exception as e:
        raise RuntimeError(f"Search failed: {str(e)}") from e

__all__ = [
    'search_web',
    'SearchProviderFactory',
    'RateLimiter',
    'SearchProvider',
    'BraveSearchProvider',
    'OxylabsSearchProvider'
]