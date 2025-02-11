"""Brave Search API provider implementation."""

from typing import List, Optional
from brave import AsyncBrave
from .base import SearchProvider

class BraveSearchProvider(SearchProvider):
    """Provider for Brave Search API with async support."""
    
    def __init__(self, api_key: Optional[str]):
        """
        Initialize Brave search provider.
        
        Args:
            api_key: Brave Search API key
        """
        self.api_key = api_key
        self.client = AsyncBrave(api_key=api_key) if api_key else None
        
    async def search(self, query: str, results: int) -> List[str]:
        """Execute search using Brave Search API."""
        if not self.client:
            return []
            
        search_results = await self.client.search(q=query, count=results)
        
        if not search_results or not search_results.web_results:
            return []
            
        return [str(item['url']) for item in search_results.web_results]
        
    def validate_credentials(self) -> bool:
        """Validate Brave API key exists."""
        return bool(self.api_key)