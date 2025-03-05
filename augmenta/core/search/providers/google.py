from typing import List
from .base import SearchProvider

class GoogleSearchProvider(SearchProvider):
    """Google Custom Search API provider."""
    
    BASE_URL = "https://customsearch.googleapis.com/customsearch/v1"
    
    def __init__(self, api_key: str | None, cx: str | None):
        super().__init__()
        self.api_key = api_key
        self.cx = cx

    async def _search_implementation(self, query: str, results: int) -> List[str]:
        """Execute search and return list of result URLs."""
        if not self.api_key or not self.cx:
            return []
            
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip"
        }
        
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": min(results, 10)  # API limit is 10 per request
        }
        
        response_data = await self._make_request(
            self.BASE_URL,
            headers=headers,
            params=params
        )
        
        if not response_data:
            return []
            
        items = response_data.get("items", [])
        return [self._normalize_url(item["link"]) for item in items]