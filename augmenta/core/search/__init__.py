"""Search functionality for web queries with rate limiting and multiple providers."""

from typing import List, Optional
from .factory import SearchProviderFactory
from ..utils import RateLimiter
from .providers import SearchProvider, BraveSearchProvider, OxylabsSearchProvider

# Singleton rate limiter for all search operations
_rate_limiter: Optional[RateLimiter] = None

async def search_web(
    query: str,
    results: int,
    engine: str,
    rate_limit: float,
    credentials: dict[str, str]
) -> List[str]:
    """
    Search the web using the specified engine with rate limiting.
    
    Args:
        query: Search query string
        results: Number of results to return (must be positive)
        engine: Search engine identifier ("brave", "oxylabs_google", "oxylabs_bing")
        rate_limit: Minimum time between requests in seconds
        credentials: API credentials for the search provider
        
    Returns:
        List of URLs from search results
        
    Raises:
        ValueError: If query is empty, results count is invalid, or credentials are invalid
        RuntimeError: If search operation fails
    """
    if not query.strip():
        raise ValueError("Search query cannot be empty")
    
    if results < 1:
        raise ValueError("Results count must be positive")
        
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(rate_limit)
        
    try:
        provider = SearchProviderFactory.create(engine, credentials)
        await _rate_limiter.acquire()
        return await provider.search(query, results)
        
    except Exception as e:
        raise RuntimeError(f"Search failed: {str(e)}") from e

__all__ = [
    'search_web',
    'SearchProviderFactory',
    'SearchProvider',
    'BraveSearchProvider', 
    'OxylabsSearchProvider'
]