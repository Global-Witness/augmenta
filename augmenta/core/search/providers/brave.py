from typing import List, Dict
from .base import SearchProvider

class BraveSearchProvider(SearchProvider):
    """Brave Search API provider."""
    
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"
    
    def __init__(self, api_key: str | None):
        super().__init__()
        self.api_key = api_key

    async def _search_implementation(self, query: str, results: int) -> List[Dict[str, str]]:
        """Execute search and return list of result URLs."""
        if not self.api_key:
            return []
            
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
        
        params = {
            "q": query,
            "count": min(results, 20)
        }
        
        response_data = await self._make_request(
            self.BASE_URL,
            headers=headers,
            params=params
        )
        
        if not response_data or not isinstance(response_data, dict):
            return []
            
        web_results = response_data.get("web", {}).get("results", [])
        return [
            {
                "url": result["url"],
                "title": result["title"],
                "description": result["description"]
            }
            for result in web_results]