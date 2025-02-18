from typing import Dict, List
from lxml import html
from random import shuffle
from .base import SearchProvider

class DuckDuckGoSearchProvider(SearchProvider):
    """DuckDuckGo Search provider implementation."""
    
    HTML_ENDPOINT = "https://html.duckduckgo.com/html"
    LITE_ENDPOINT = "https://lite.duckduckgo.com/lite/"
    
    def __init__(self, region: str | None = None, safesearch: str = "moderate", **kwargs):
        """Initialize DuckDuckGo search provider."""
        super().__init__(**kwargs)
        self.region = region or "wt-wt"
        self.safesearch = safesearch

    async def _extract_results(self, response_text: str, endpoint: str, max_results: int) -> List[Dict[str, str]]:
        """Extract results from HTML response."""
        if not response_text:
            return []
            
        tree = html.fromstring(response_text)
        results = []
        seen_urls = set()
        
        if endpoint == self.HTML_ENDPOINT:
            elements = tree.xpath("//div[contains(@class, 'result')]")
            for element in elements:
                url_elem = element.xpath(".//a[@class='result__url']/@href")
                if not url_elem:
                    continue
                    
                url = self._normalize_url(url_elem[0])
                if url in seen_urls or "duckduckgo.com/y.js?ad" in url:
                    continue
                    
                seen_urls.add(url)
                results.append({"href": url})
                
                if len(results) >= max_results:
                    break
        else:  # LITE_ENDPOINT
            rows = tree.xpath("//table[@class='results']//tr[.//a]")
            for row in rows:
                url_elem = row.xpath(".//a/@href")
                if not url_elem:
                    continue
                    
                url = self._normalize_url(url_elem[0])
                if url in seen_urls or "duckduckgo.com/y.js?ad" in url:
                    continue
                    
                seen_urls.add(url)
                results.append({"href": url})
                
                if len(results) >= max_results:
                    break
                    
        return results

    async def search(self, query: str, results: int) -> List[str]:
        """Execute search and return list of result URLs."""
        payload = {
            "q": query,
            "s": "0",
            "o": "json",
            "api": "d.js",
            "kl": self.region,
            **self.kwargs
        }
        
        # Try both backends in random order
        backends = [(self.HTML_ENDPOINT, "POST"), (self.LITE_ENDPOINT, "POST")]
        shuffle(backends)
        
        headers = {"User-Agent": "Mozilla/5.0"}
        
        for endpoint, method in backends:
            response_text = await self._make_request(
                endpoint,
                method=method,
                headers=headers,
                data=payload
            )
            
            if response_text:
                search_results = await self._extract_results(response_text, endpoint, results)
                if search_results:
                    return [result["href"] for result in search_results]
                    
        return []