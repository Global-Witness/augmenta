from typing import List, Literal
from oxylabs import AsyncClient
from .base import SearchProvider

EngineType = Literal["google", "bing"]

class OxylabsSearchProvider(SearchProvider):
    def __init__(self, username: str | None, password: str | None, engine: EngineType = "google"):
        self.engine = engine
        self.client = AsyncClient(username, password) if username and password else None
        
    async def search(self, query: str, results: int) -> List[str]:
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