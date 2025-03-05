from abc import ABC, abstractmethod
from typing import Optional, List
import httpx
import logging
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
from augmenta.utils.limiter import RateLimitManager

logger = logging.getLogger(__name__)

class SearchProvider(ABC):
    """Base search provider with common functionality."""
    
    def __init__(self):
        """Initialize search provider."""
        logger.debug(f"Initialized {self.__class__.__name__}")

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL by removing tracking parameters."""
        return url.split("?")[0] if "?" in url else url

    async def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[dict | str]:
        """Make HTTP request with retry logic."""
        logger.debug(f"Making {method} request to {url}")
        async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_fixed(2)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method,
                        url,
                        follow_redirects=True,
                        timeout=10.0,
                        **kwargs
                    )
                    response.raise_for_status()
                    return (response.json() if response.headers.get('content-type', '').startswith('application/json')
                           else response.text)
        
        logger.error("Request failed after 3 attempts")
        return None

    @abstractmethod
    async def _search_implementation(self, query: str, results: int) -> List[str]:
        """Provider-specific search implementation."""
        pass

    async def search(self, query: str, results: int, rate_limit: Optional[float] = None) -> List[str]:
        """Execute search with rate limiting."""
        rate_limit = 0 if rate_limit is None else rate_limit
        
        async with RateLimitManager.acquire(self.__class__.__name__, rate_limit=rate_limit):
            return await self._search_implementation(query, results)