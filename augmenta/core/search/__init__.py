from typing import List
from .factory import SearchProviderFactory
from augmenta.utils.utils import RateLimiter
from .providers import (
    SearchProvider, 
    BraveSearchProvider,
    DuckDuckGoSearchProvider,
    OxylabsSearchProvider
)

_rate_limiter: RateLimiter | None = None

async def search_web(
    query: str,
    results: int,
    engine: str,
    rate_limit: float,
    credentials: dict[str, str]
) -> List[str]:
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
    'SearchProvider',
    'BraveSearchProvider',
    'DuckDuckGoSearchProvider',
    'OxylabsSearchProvider'
]