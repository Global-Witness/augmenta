from typing import List, Literal, Dict, Any, Optional
from augmenta.core.config.credentials import CredentialsManager
from .providers import (
    BraveSearchProvider,
    GoogleSearchProvider,
    DuckDuckGoSearchProvider
)
import logging
logger = logging.getLogger(__name__)

# Default configuration for AI agent use
DEFAULT_ENGINE: Literal["brave", "google", "duckduckgo"] = "brave"
DEFAULT_RESULTS = 5

def _get_credentials() -> Dict[str, str]:
    """Get credentials using CredentialsManager."""
    config = {'search': {'engine': DEFAULT_ENGINE}}
    try:
        return CredentialsManager().get_credentials(config)
    except ValueError:
        return {
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
) -> List[Dict[str, str]]:
    """Internal implementation of web search with full configuration."""
    print(f"_search_web_impl: engine={engine}, credentials={credentials}")
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
async def search_web(query: str) -> str:
    """Search the web for information.
    
    Performs a web search using the configured search engine and returns markdown formatted results.
    
    Args:
        query: The search query string. This should be a specific question or topic
               that you want to find information about.
               
    Returns:
        A markdown formatted string containing search results with titles and descriptions.
        
    Example:
        >>> await search_web("latest developments in quantum computing")
        '## Search Results\n\n[Title](url)\nDescription'
    """
    credentials = _get_credentials()
    print(f"search_web: credentials={credentials}")
    
    results = await _search_web_impl(
        query=query,
        results=DEFAULT_RESULTS,
        engine=DEFAULT_ENGINE,
        credentials=credentials
    )
    print(f"search_web: got {len(results)} results")
    
    markdown_results = [f"[{r['title']}]({r['url']})\n{r['description']}" for r in results]
    return "## Search Results\n\n" + "\n\n".join(markdown_results)

# For backward compatibility and programmatic use
__all__ = ['search_web', '_search_web_impl']