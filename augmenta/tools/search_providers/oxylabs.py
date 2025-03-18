from typing import List, Dict
from .base import SearchProvider

class OxylabsSearchProvider(SearchProvider):
    """Oxylabs Google Search API provider."""
    
    required_credentials = {'OXYLABS_USERNAME', 'OXYLABS_PASSWORD'}
    BASE_URL = "https://realtime.oxylabs.io/v1/queries"
    
    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self.username = credentials.get('OXYLABS_USERNAME')
        self.password = credentials.get('OXYLABS_PASSWORD')

    async def _search_implementation(self, query: str, results: int) -> List[Dict[str, str]]:
        """Execute search and return list of result URLs."""
        if not self.username or not self.password:
            return []
            
        auth = (self.username, self.password)
        headers = {
            "Content-Type": "application/json",
        }
        
        json_data = {
            "source": "google_search",
            "query": query,
            "parse": True,
            "limit": min(results, 20),
            "context": [{"key": "filter", "value": 1}]
        }
        
        response_data = await self._make_request(
            self.BASE_URL,
            method="POST",
            auth=auth,
            headers=headers,
            json=json_data
        )
        
        if not response_data or not isinstance(response_data, dict):
            return []
            
        results = response_data.get("results", [])
        if not results:
            return []
            
        content = results[0].get("content", {})
        results_data = content.get("results", {})
        organic_results = results_data.get("organic", [])
        
        return [
            {
                "url": result.get("url", ""),
                "title": result.get("title", ""),
                "description": result.get("desc", "")
            }
            for result in organic_results]