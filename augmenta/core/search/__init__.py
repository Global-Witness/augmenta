from typing import List, Literal, Dict, Any, Optional, Set
from augmenta.core.config.credentials import CredentialsManager
from .providers import PROVIDERS, create_provider

# logging
import logging
import logfire
logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()])
logger = logging.getLogger(__name__)

# Default configuration for AI agent use
DEFAULT_ENGINE: Literal["brave", "google", "duckduckgo", "oxylabs_google", "brightdata_google"] = "duckduckgo"
DEFAULT_RESULTS = 20

_credentials_manager = CredentialsManager()

async def _search_web_impl(
    query: str,
    results: int,
    engine: Literal["brave", "google", "duckduckgo", "oxylabs_google", "brightdata_google"],
    credentials: dict[str, str],
    rate_limit: Optional[float] = None,
    search_config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """Internal implementation of web search with full configuration."""
    if not query.strip():
        raise ValueError("Search query cannot be empty")
    
    if results < 1:
        raise ValueError("Results count must be positive")
    
    logger.info(f"Trying to search for: {query}")

    try:
        provider = create_provider(engine, credentials)
    except ValueError as e:
        logging.error(f"Failed to create provider: {e}")
        return []
        
    return await provider.search(query, results, rate_limit)

# @agent.tool_plain
async def search_web(query: str, engine: Optional[str] = None) -> str:
    """Search the web for information.
    
    Performs a web search using the configured search engine and returns markdown formatted results.
    
    Args:
        query: The search query string. This should be a specific question or topic
               that you want to find information about.
        engine: Optional search engine override. If not provided, uses DEFAULT_ENGINE.
               
    Returns:
        A markdown formatted string containing search results with titles and descriptions.
        
    Example:
        >>> await search_web("latest developments in quantum computing")
        '## Search Results\n\n[Title](url)\nDescription'
    """
    current_engine = engine or DEFAULT_ENGINE
    try:
        credentials = _credentials_manager.get_credentials(
            PROVIDERS[current_engine].required_credentials
        )
    except KeyError:
        logging.error(f"Unsupported search engine: {current_engine}")
        credentials = {}
    except ValueError:
        logging.warning(
            f"Could not get credentials for {current_engine}. Proceeding without credentials."
        )
        credentials = {}
        
    results = await _search_web_impl(
        query=query,
        results=DEFAULT_RESULTS,
        engine=current_engine,
        credentials=credentials,
    )
    
    markdown_results = [f"[{r['title']}]({r['url']})\n{r['description']}" for r in results]
    return "## Search Results\n\n" + "\n\n".join(markdown_results)

# For backward compatibility and programmatic use
__all__ = ['search_web', '_search_web_impl']