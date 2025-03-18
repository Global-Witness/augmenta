"""Search functionality for the Augmenta package."""

from typing import Dict, List, Any, Optional
from .providers import PROVIDERS
from ...config.credentials import CredentialsManager

async def _search_web_impl(
    query: str,
    results: int,
    engine: str,
    rate_limit: Optional[float] = None,
    search_config: Dict[str, Any] = None
) -> List[Dict[str, str]]:
    """Implementation of web search functionality.
    
    Args:
        query: Search query string
        results: Number of results to return
        engine: Search engine to use
        rate_limit: Optional rate limit in seconds
        search_config: Additional search configuration options
        
    Returns:
        List of search results with 'url' and 'title' fields
    """
    try:
        provider_class = PROVIDERS[engine]
        credentials_manager = CredentialsManager()
        credentials = credentials_manager.get_credentials(provider_class.required_credentials)
        search_provider = provider_class(credentials=credentials)
        search_results = await search_provider._search_implementation(
            query=query,
            results=results
        )
        return search_results
        
    except Exception as e:
        # Log error and return empty results
        import logging
        logging.error(f"Search error: {str(e)}")
        return []