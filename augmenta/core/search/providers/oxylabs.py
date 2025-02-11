"""Oxylabs SERP API provider implementation."""

from typing import List, Literal
from oxylabs import AsyncClient
from .base import SearchProvider

EngineType = Literal["google", "bing"]

class OxylabsSearchProvider(SearchProvider):
    """Provider for Oxylabs SERP API with support for Google and Bing."""
    
    def __init__(self, username: str, password: str, engine: EngineType = "google"):
        """
        Initialize Oxylabs search provider.
        
        Args:
            username: Oxylabs username
            password: Oxylabs password
            engine: Search engine to use ("google" or "bing")
        """
        self.username = username
        self.password = password
        self.engine = engine
        self.client = AsyncClient(username, password) if username and password else None
        
    async def search(self, query: str, results: int) -> List[str]:
        """Execute search using Oxylabs SERP API."""
        if not self.client:
            return []
            
        scrape_method = (
            self.client.serp.google.scrape_search if self.engine == "google"
            else self.client.serp.bing.scrape_search
        )
        
        result = await scrape_method(
            query,
            parse=True,
            limit=results,
            timeout=35,
            poll_interval=3,
        )
        
        if not result or not result.results:
            return []
            
        return [
            item['url'] for item in result.results.get('organic', [])[:results]
            if 'url' in item
        ]
        
    def validate_credentials(self) -> bool:
        """Validate Oxylabs credentials exist."""
        return bool(self.username and self.password)