from typing import List
from oxylabs import AsyncClient
from .base import SearchProvider

class OxylabsSearchProvider(SearchProvider):
    def __init__(self, username: str, password: str, engine: str = "google"):
        self.username = username
        self.password = password
        self.engine = engine
        self.client = AsyncClient(username, password)
        
    async def search(self, query: str, results: int) -> List[str]:
        if self.engine == "google":
            result = await self.client.serp.google.scrape_search(
                query,
                parse=True,
                limit=results,
                timeout=35,
                poll_interval=3,
            )
        else:  # bing
            result = await self.client.serp.bing.scrape_search(
                query,
                parse=True,
                limit=results,
                timeout=35,
                poll_interval=3,
            )
            
        if not result or not result.results:
            return []
            
        urls = []
        for item in result.results.get('organic', [])[:results]:
            if 'url' in item:
                urls.append(item['url'])
        return urls
        
    def validate_credentials(self) -> bool:
        return bool(self.username and self.password)