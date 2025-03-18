from typing import List, Dict
from .base import SearchProvider

class GoogleSearchProvider(SearchProvider):
    """Google Custom Search API provider."""
    
    required_credentials = {'GOOGLE_API_KEY', 'GOOGLE_CX'}
    BASE_URL = "https://customsearch.googleapis.com/customsearch/v1"
    
    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self.api_key = credentials.get('GOOGLE_API_KEY')
        self.cx = credentials.get('GOOGLE_CX')

    async def _search_implementation(self, query: str, results: int) -> List[Dict[str, str]]:
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
        return [
            {
                "url": self._normalize_url(item["link"]),
                "title": item.get("title", ""),
                "description": item.get("snippet", "")
            }
            for item in items]