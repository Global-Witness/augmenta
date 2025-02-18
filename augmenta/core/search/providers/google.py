from typing import Dict, List
from .base import SearchProvider

class GoogleSearchProvider(SearchProvider):
    """Google Custom Search API provider implementation."""
    
    BASE_URL = "https://customsearch.googleapis.com/customsearch/v1"
    
    def __init__(self, api_key: str | None, cx: str | None, **kwargs):
        """Initialize Google Custom Search provider.
        
        Args:
            api_key: Google API key
            cx: Custom Search Engine ID
            **kwargs: Additional parameters to pass to the API
        """
        super().__init__(**kwargs)
        self.api_key = api_key
        self.cx = cx

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare request headers."""
        return {
            "Accept": "application/json",
            "Accept-Encoding": "gzip"
        }

    async def search(self, query: str, results: int) -> List[str]:
        """Execute search and return list of result URLs.
        
        Args:
            query: Search query string
            results: Number of results to return (max 10 per request)
            
        Returns:
            List of result URLs
        """
        if not self.api_key or not self.cx:
            return []

        all_urls = []
        remaining_results = min(results, 100)  # API limit is 100 results total
        
        while remaining_results > 0:
            # Calculate start index for pagination
            start_index = len(all_urls) + 1
            
            # Calculate number of results for this request (max 10 per request)
            current_count = min(remaining_results, 10)
            
            params = {
                "key": self.api_key,
                "cx": self.cx,
                "q": query,
                "num": current_count,
                "start": start_index,
                **self.kwargs
            }
            
            response_data = await self._make_request(
                self.BASE_URL,
                headers=self._prepare_headers(),
                params=params
            )
            
            if not response_data:
                break
                
            items = response_data.get("items", [])
            if not items:
                break
                
            # Extract and normalize URLs
            urls = [self._normalize_url(item["link"]) for item in items]
            all_urls.extend(urls)
            
            remaining_results -= len(urls)
            
            # If we got fewer results than requested, there are no more results
            if len(urls) < current_count:
                break
        
        return all_urls