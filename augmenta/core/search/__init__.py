from typing import List, Dict, Any
from .factory import SearchProviderFactory
from augmenta.utils.utils import RateLimiter
from .providers import (
    SearchProvider, 
    BraveSearchProvider,
    GoogleSearchProvider,
    DuckDuckGoSearchProvider,
    OxylabsSearchProvider
)

_rate_limiter: RateLimiter | None = None

async def search_web(
    query: str,
    results: int,
    engine: str,
    rate_limit: float,
    credentials: dict[str, str],
    search_config: Dict[str, Any]
) -> List[str]:
    if not query.strip():
        raise ValueError("Search query cannot be empty")
    
    if results < 1:
        raise ValueError("Results count must be positive")
        
    try:
        # Remove the global rate limiter here - we'll use the provider's one
        provider = SearchProviderFactory.create(engine, credentials, search_config)
        return await provider.search(query, results)
        
    except Exception as e:
        raise RuntimeError(f"Search failed: {str(e)}") from e


__all__ = [
    'search_web',
    'SearchProvider',
    'BraveSearchProvider',
    'GoogleSearchProvider',
    'DuckDuckGoSearchProvider',
    'OxylabsSearchProvider'
]