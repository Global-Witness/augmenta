from abc import ABC, abstractmethod, abstractproperty
from typing import Optional, List, Dict, Set, ClassVar, Dict, Any, Union
import httpx
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
from augmenta.utils.limiter import RateLimitManager

# logging
import logging
import logfire
logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()])
logger = logging.getLogger(__name__)

class SearchProvider(ABC):
    """Base search provider with common functionality."""

    required_credentials: ClassVar[Set[str]] = set()

    def __init__(self, credentials: Dict[str, str]):
        """Initialize search provider.
        
        Args:
            credentials: Dictionary of credential key-value pairs
        """
        logger.debug(f"Initialized {self.__class__.__name__}")
        self._init_credentials(credentials)

    def _init_credentials(self, credentials: Dict[str, str]) -> None:
        """Initialize provider with required credentials.
        
        Args:
            credentials: Dictionary of credential key-value pairs
        """
        missing = self.required_credentials - credentials.keys()
        if missing:
            raise ValueError(f"Missing required credentials: {missing}")

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL by removing tracking parameters."""
        return url.split("?")[0] if "?" in url else url

    async def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[Union[dict, str]]:
        """Make HTTP request with retry logic."""
        logger.debug(f"Making {method} request to {url}")
        async for attempt in AsyncRetrying(stop=stop_after_attempt(3), wait=wait_fixed(2)):
            with attempt:
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method,
                        url,
                        follow_redirects=True,
                        timeout=20.0,
                        **kwargs
                    )
                    response.raise_for_status()
                    return (response.json() if response.headers.get('content-type', '').startswith('application/json')
                           else response.text)
        
        logger.error("Request failed after 3 attempts")
        return None

    @abstractmethod
    async def _search_implementation(self, query: str, results: int) -> List[Dict[str, str]]:
        """Provider-specific search implementation. Returns list of dicts with 'url', 'title', and 'description'."""
        pass

    async def search(self, query: str, results: int, rate_limit: Optional[float] = None) -> List[Dict[str, str]]:
        """Execute search with optional rate limiting."""
        if rate_limit is not None and rate_limit > 0:
            async with RateLimitManager.acquire(self.__class__.__name__, rate_limit=rate_limit):
                return await self._search_implementation(query, results)
        return await self._search_implementation(query, results)