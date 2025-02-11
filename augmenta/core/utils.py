"""
Utility functions and classes for the Augmenta package.
"""

import json
import hashlib
import asyncio
import time
from typing import Dict, Optional, ClassVar
from dataclasses import dataclass

def get_config_hash(config: dict) -> str:
    """
    Generate a deterministic hash of configuration data.
    
    Args:
        config: Configuration dictionary to hash
        
    Returns:
        str: SHA-256 hash of the sorted JSON representation
    """
    if not isinstance(config, dict):
        raise TypeError("Config must be a dictionary")
        
    return hashlib.sha256(
        json.dumps(config, sort_keys=True).encode('utf-8')
    ).hexdigest()

@dataclass
class RateLimiter:
    """
    Rate limiter for API requests using singleton pattern.
    
    Args:
        rate_limit: Minimum time (seconds) between requests. None for no limit.
    """
    rate_limit: Optional[float]
    
    # Class variables
    _instances: ClassVar[Dict[Optional[float], 'RateLimiter']] = {}
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _last_request_time: float = 0.0
    
    def __new__(cls, rate_limit: Optional[float] = None) -> 'RateLimiter':
        if rate_limit not in cls._instances:
            instance = super().__new__(cls)
            instance.rate_limit = rate_limit
            cls._instances[rate_limit] = instance
        return cls._instances[rate_limit]
        
    async def acquire(self) -> None:
        """Wait for rate limit if needed."""
        if self.rate_limit is None:
            return
            
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self.rate_limit:
                await asyncio.sleep(self.rate_limit - time_since_last)
                
            self._last_request_time = time.time()