from typing import List, Dict
from lxml import html
from .base import SearchProvider

class DuckDuckGoSearchProvider(SearchProvider):
    """DuckDuckGo Search provider."""
    
    required_credentials = set()  # No credentials needed
    HTML_ENDPOINT = "https://html.duckduckgo.com/html"
    
    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)

    async def _search_implementation(self, query: str, results: int) -> List[Dict[str, str]]:
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
        
        search_results = []
        seen_urls = set()
        
        for element in elements:
            if len(search_results) >= results:
                break
                
            url_elem = element.xpath(".//a[@class='result__url']/@href")
            title_elem = element.xpath(".//h2[@class='result__title']/a/text()")
            desc_elem = element.xpath(".//div[contains(@class, 'result__snippet')]/text()")
            
            if not url_elem or not title_elem:
                continue
                
            url = self._normalize_url(url_elem[0])
            if url in seen_urls or "duckduckgo.com/y.js?ad" in url:
                continue
                
            search_results.append({
                "url": url,
                "title": title_elem[0].strip(),
                "description": desc_elem[0].strip() if desc_elem else ""
            })
            seen_urls.add(url)
        
        return search_results