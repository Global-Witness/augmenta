from typing import List
from lxml import html
from .base import SearchProvider

class DuckDuckGoSearchProvider(SearchProvider):
    """DuckDuckGo Search provider."""
    
    HTML_ENDPOINT = "https://html.duckduckgo.com/html"
    
    def __init__(self):
        super().__init__()

    async def _search_implementation(self, query: str, results: int) -> List[str]:
        """Execute search and return list of result URLs."""
        headers = {"User-Agent": "Mozilla/5.0"}
        payload = {
            "q": query,
            "s": "0",
            "o": "json",
            "api": "d.js"
        }
        
        response_text = await self._make_request(
            self.HTML_ENDPOINT,
            method="POST",
            headers=headers,
            data=payload
        )
        
        if not response_text:
            return []
            
        tree = html.fromstring(response_text)
        elements = tree.xpath("//div[contains(@class, 'result')]")
        
        urls = []
        seen_urls = set()
        
        for element in elements:
            if len(urls) >= results:
                break
                
            url_elem = element.xpath(".//a[@class='result__url']/@href")
            if not url_elem:
                continue
                
            url = self._normalize_url(url_elem[0])
            if url in seen_urls or "duckduckgo.com/y.js?ad" in url:
                continue
                
            seen_urls.add(url)
            urls.append(url)
        
        return urls