from typing import Dict, List
from .base import SearchProvider

class BrightDataSearchProvider(SearchProvider):
    """Bright Data API provider implementation."""
    
    BASE_URL = "https://api.brightdata.com/request"
    
    def __init__(self, api_key: str | None, zone: str = "augmenta", **kwargs):
        """Initialize Bright Data search provider."""
        super().__init__(**kwargs)
        self.api_key = api_key
        self.zone = zone
    
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare request headers."""
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def search(self, query: str, results: int) -> List[str]:
        """Execute search and return list of result URLs."""
        if not self.api_key:
            return []
            
        json_data = {
            "zone": self.zone,
            "url": f"https://www.google.com/search?q={query}&brd_json=1",
            "format": "raw"
        }
        
        response_data = await self._make_request(
            self.BASE_URL,
            headers=self._prepare_headers(),
            method="POST",
            json=json_data
        )
        
        if not response_data:
            return []
        
        organic_results = response_data.get("organic", [])
        return [result["link"] for result in organic_results]