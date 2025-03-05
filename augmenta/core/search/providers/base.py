from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import httpx
import logging
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
from augmenta.utils.limiter import RateLimitManager

logger = logging.getLogger(__name__)

class SearchProvider(ABC):
    """Base search provider with common functionality."""
    
    def __init__(self, rate_limit: Optional[float] = None, **kwargs):
        """Initialize search provider with common parameters."""
        self.kwargs = kwargs
        self.rate_limit = rate_limit
        logger.debug(f"Initialized {self.__class__.__name__} with rate limit: {rate_limit}s")

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL by removing tracking parameters."""
        return url.split("?")[0] if "?" in url else url

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text by removing extra whitespace."""
        return " ".join(text.split())

    async def _make_request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_attempts: int = 3,
        retry_delay: int = 2
    ) -> Optional[Dict | str]:
        """Make HTTP request with retry logic.
        
        Args:
            url: Request URL
            method: HTTP method (GET/POST)
            headers: Request headers
            params: Query parameters for GET requests
            data: POST data
            retry_attempts: Number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Response data (JSON or text) or None if request fails
        """
        logger.debug(f"Making {method} request to {url}")
        
        # Default to 2 seconds between requests when rate_limit is None
        rate_limit = 0 if self.rate_limit is None else self.rate_limit
        
        async with RateLimitManager.acquire(
            self.__class__.__name__,
            rate_limit=rate_limit
        ):
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(retry_attempts),
                wait=wait_fixed(retry_delay)
            ):
                with attempt:
                    async with httpx.AsyncClient() as client:
                        logger.debug(f"Sending request (attempt {attempt.retry_state.attempt_number})")
                        response = await client.request(
                            method,
                            url,
                            headers=headers,
                            params=params,
                            data=data,
                            follow_redirects=True,
                            timeout=10.0
                        )
                        response.raise_for_status()
                        logger.debug(f"Request successful with status {response.status_code}")
                        return (response.json() if response.headers.get('content-type', '').startswith('application/json')
                               else response.text)
            
            logger.error(f"Request failed after {retry_attempts} attempts")
            return None

    @abstractmethod
    async def search(self, query: str, results: int) -> List[str]:
        """Execute search and return list of result URLs."""
        pass