from typing import List
from duckduckgo_search import DDGS
from .base import SearchProvider

class DuckDuckGoSearchProvider(SearchProvider):
    def __init__(self, region: str | None = None, safesearch: str = "moderate", **kwargs):
        self.region = region or "wt-wt"
        self.safesearch = safesearch
        self.client = DDGS()
        self.kwargs = kwargs
        
    async def search(self, query: str, results: int) -> List[str]:
        try:
            search_results = self.client.text(
                keywords=query,
                region=self.region,
                safesearch=self.safesearch,
                max_results=results,
                **self.kwargs
            )
            
            if not search_results:
                return []
                
            return [result['href'] for result in search_results]
            
        except Exception as e:
            # Log error if needed
            return []