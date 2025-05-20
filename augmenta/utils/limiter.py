"""Rate limiting implementation using aiolimiter."""

from contextlib import asynccontextmanager
from aiolimiter import AsyncLimiter
from typing import Dict, Optional, ClassVar

# logging
import logging
import logfire
logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()])
logger = logging.getLogger(__name__)

class RateLimitManager:
    """Global rate limiter manager using aiolimiter.
    
    This class provides a thread-safe way to manage rate limiters for different services.
    It ensures consistent rate limiting across async processes by maintaining singleton
    instances of limiters for each service.
    """
    
    # Class variable to store limiter instances
    _instances: ClassVar[Dict[str, AsyncLimiter]] = {}
    
    @classmethod
    def get_limiter(
        cls,
        name: str,
        rate_limit: float
    ) -> AsyncLimiter:
        """Get or create a rate limiter for a specific service.
        
        Args:
            name: Name of the service/provider requiring rate limiting
            rate_limit: Time between requests in seconds (e.g. 2.0 for one request per 2 seconds)
            
        Returns:
            AsyncLimiter instance for the specified service
        """
        # For rate_limit=2.0 (1 request per 2 seconds):
        # - max_rate = 1 request
        # - time_period = 2 seconds
        max_rate = 1
        time_period = rate_limit
        
        key = f"{name}:{rate_limit}"
        if key not in cls._instances:
            logger.debug(
                f"Creating new limiter for {name} "
                f"(1 request per {rate_limit}s)"
            )
            cls._instances[key] = AsyncLimiter(max_rate, time_period)
        return cls._instances[key]
    
    @classmethod
    @asynccontextmanager
    async def acquire(
        cls,
        name: str,
        rate_limit: float
    ):
        """Context manager for rate limiting.
        
        Args:
            name: Name of the service/provider requiring rate limiting
            rate_limit: Time between requests in seconds (e.g. 2.0 for one request per 2 seconds)
            
        Yields:
            None after acquiring the rate limit
            
        Example:
            >>> async with RateLimitManager.acquire("api", 2.0):  # 1 req/2s
            >>>     response = await make_api_request()
        """
        limiter = cls.get_limiter(name, rate_limit)
        try:
            async with limiter:
                logger.debug(f"Acquired rate limit for {name}")
                yield
        except Exception as e:
            logger.error(f"Error while rate limited for {name}: {e}")
            raise