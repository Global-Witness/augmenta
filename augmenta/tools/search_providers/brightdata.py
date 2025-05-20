from typing import List, Dict
from .base import SearchProvider


class BrightDataSearchProvider(SearchProvider):
    """BrightData Google Search API provider."""
    
    required_credentials = {'BRIGHTDATA_API_KEY', 'BRIGHTDATA_ZONE'}
    BASE_URL = "https://api.brightdata.com/request"
    
    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self.api_key = credentials.get('BRIGHTDATA_API_KEY')
        self.zone = credentials.get('BRIGHTDATA_ZONE')

    async def _search_implementation(self, query: str, results: int) -> List[Dict[str, str]]:
        """Execute search and return list of result URLs."""
        if not self.api_key:
            return []
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        from urllib.parse import quote
        
        json_data = {
            "zone": self.zone,
            "url": f"https://www.google.com/search?q={quote(query)}&num={min(results, 20)}&brd_json=1",
            "format": "raw"
        }
        
        response_data = await self._make_request(
            self.BASE_URL,
            method="POST",
            headers=headers,
            json=json_data
        )
        
        if not response_data or not isinstance(response_data, dict):
            return []
            
        organic_results = response_data.get("organic", [])
        
        return [
            {
                "url": result.get("link", ""),
                "title": result.get("title", ""),
                "description": result.get("description", "")
            }
            for result in organic_results]