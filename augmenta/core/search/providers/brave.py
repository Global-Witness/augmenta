from typing import Dict, List
from .base import SearchProvider

class BraveSearchProvider(SearchProvider):
    """Brave Search API provider implementation."""
    
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"
    
    def __init__(self, api_key: str | None, **kwargs):
        """Initialize Brave search provider."""
        super().__init__(**kwargs)
        self.api_key = api_key

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare request headers."""
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip"
        }
        if self.api_key:
            headers["X-Subscription-Token"] = self.api_key
        return headers

    async def search(self, query: str, results: int) -> List[str]:
        """Execute search and return list of result URLs."""
        if not self.api_key:
            return []
            
        params = {
            "q": query,
            "count": min(results, 20),
            **self.kwargs
        }
        
        response_data = await self._make_request(
            self.BASE_URL,
            headers=self._prepare_headers(),
            params=params
        )
        
        if not response_data:
            return []
            
        web_results = response_data.get("web", {}).get("results", [])
        return [result["url"] for result in web_results]