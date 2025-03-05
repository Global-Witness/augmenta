from typing import List, Literal, Dict, Any, Optional
from .providers import (
    BraveSearchProvider,
    GoogleSearchProvider,
    DuckDuckGoSearchProvider
)

# Default configuration for AI agent use
DEFAULT_ENGINE: Literal["brave", "google", "duckduckgo"] = "brave"
DEFAULT_RESULTS = 5

# Credentials should be configured via environment variables or settings
CREDENTIALS: Dict[str, str] = {
    "BRAVE_API_KEY": None,
    "GOOGLE_API_KEY": None,
    "GOOGLE_CX": None
}

async def _search_web_impl(
    query: str,
    results: int,
    engine: Literal["brave", "google", "duckduckgo"],
    credentials: dict[str, str],
    rate_limit: Optional[float] = None,
    search_config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Internal implementation of web search with full configuration."""
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

# @agent.tool_plain
async def search_web(query: str) -> List[str]:
    """Search the web for information.
    
    Performs a web search using the configured search engine and returns a list of relevant URLs.
    
    Args:
        query: The search query string. This should be a specific question or topic
               that you want to find information about.
               
    Returns:
        A list of URLs containing relevant information for the query.
        
    Example:
        >>> await search_web("latest developments in quantum computing")
        ['https://example.com/quantum-news', 'https://example.com/research']
    """
    return await _search_web_impl(
        query=query,
        results=DEFAULT_RESULTS,
        engine=DEFAULT_ENGINE,
        credentials=CREDENTIALS
    )

# For backward compatibility and programmatic use
__all__ = ['search_web', '_search_web_impl']