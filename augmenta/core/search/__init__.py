from typing import List, Literal, Dict, Any, Optional
from .providers import (
    BraveSearchProvider,
    GoogleSearchProvider,
    DuckDuckGoSearchProvider
)

EngineType = Literal["brave", "google", "duckduckgo"]

async def search_web(
    query: str,
    results: int,
    engine: EngineType,
    credentials: dict[str, str],
    rate_limit: Optional[float] = None,
    search_config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Execute a web search using the specified engine.
    
    Args:
        query: Search query string
        results: Number of results to return
        engine: Search engine to use ("brave", "google", "duckduckgo")
        credentials: API keys and other credentials needed by the engine
        rate_limit: Optional rate limit in seconds between requests
        search_config: Optional additional configuration (not used currently)
        
    Returns:
        List of result URLs
    """
    if not query.strip():
        raise ValueError("Search query cannot be empty")
    
    if results < 1:
        raise ValueError("Results count must be positive")
    
    providers = {
        "brave": lambda: BraveSearchProvider(
            api_key=credentials.get("BRAVE_API_KEY")
        ),
        "google": lambda: GoogleSearchProvider(
            api_key=credentials.get("GOOGLE_API_KEY"),
            cx=credentials.get("GOOGLE_CX")
        ),
        "duckduckgo": lambda: DuckDuckGoSearchProvider()
    }
    
    if engine not in providers:
        raise ValueError(f"Unsupported search engine: {engine}")
    
    provider = providers[engine]()
    return await provider.search(query, results, rate_limit)

__all__ = ['search_web']