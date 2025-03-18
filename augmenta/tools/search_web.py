"""Search functionality for the Augmenta package."""

from typing import Dict, List
from .search_providers import PROVIDERS
from ..config.credentials import CredentialsManager
from ..config.read_config import get_config

async def search_web(query: str) -> List[Dict[str, str]]:
    """Web search functionality using configured provider.
    
    Args:
        query: Search query string
        
    Returns:
        List of search results with 'url' and 'title' fields
    """
    try:
        config = get_config()
        search_config = config.get("search", {})
        engine = search_config.get("engine")
        results = search_config.get("results", 5)

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