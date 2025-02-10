import asyncio
import time
from typing import Dict

class RateLimiter:
    """Rate limiter for API requests"""
    
    # Singleton instance storage
    _instances: Dict[float, 'RateLimiter'] = {}
    _lock = asyncio.Lock()
    _last_request_time: float = 0.0
    
    def __new__(cls, rate_limit: float = 1.0):
        if rate_limit not in cls._instances:
            cls._instances[rate_limit] = super(RateLimiter, cls).__new__(cls)
            cls._instances[rate_limit].rate_limit = rate_limit
        return cls._instances[rate_limit]
        
    async def acquire(self) -> None:
        """Wait for rate limit if needed"""
        async with self._lock:
            current_time = time.time()
            time_since_last_request = current_time - self._last_request_time
            
            if time_since_last_request < self.rate_limit:
                await asyncio.sleep(self.rate_limit - time_since_last_request)
                
            self._last_request_time = time.time()