from typing import List
from brave import AsyncBrave
from .base import SearchProvider

class BraveSearchProvider(SearchProvider):
    def __init__(self, api_key: str | None):
        self.client = AsyncBrave(api_key=api_key) if api_key else None
        
    async def search(self, query: str, results: int) -> List[str]:
        if not self.client:
            return []
            
        search_results = await self.client.search(q=query, count=results)
        
        if not search_results or not search_results.web_results:
            return []
            
        return [str(item['url']) for item in search_results.web_results]