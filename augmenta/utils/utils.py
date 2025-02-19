"""Utility functions and classes for the Augmenta package."""

import json
import hashlib
import asyncio
import time
import logging
from pathlib import Path
from typing import Dict, Optional, ClassVar, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

def get_hash(data: Union[dict, Path, str], chunk_size: int = 8192) -> str:
    """Generate a deterministic hash of data or file contents."""
    hasher = hashlib.sha256()
    
    if isinstance(data, dict):
        hasher.update(json.dumps(data, sort_keys=True).encode('utf-8'))
    elif isinstance(data, (str, Path)):
        filepath = Path(data)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
            
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
    else:
        raise TypeError("Data must be a dictionary, Path, or string filepath")
        
    return hasher.hexdigest()

@dataclass
class RateLimiter:
    """Rate limiter for API requests using singleton pattern."""
    rate_limit: Optional[float]
    namespace: str = "default"  # Add this field to the dataclass
    _instances: ClassVar[Dict[str, 'RateLimiter']] = {}
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _last_request_times: ClassVar[Dict[str, float]] = {}
    
    def __new__(cls, rate_limit: Optional[float] = None, namespace: str = "default") -> 'RateLimiter':
        key = f"{namespace}:{rate_limit}"
        if key not in cls._instances:
            instance = super().__new__(cls)
            instance.rate_limit = rate_limit
            instance.namespace = namespace
            cls._instances[key] = instance
            cls._last_request_times[key] = 0.0
            logger.debug(f"Created new RateLimiter instance for {namespace} with rate limit: {rate_limit}s")
        return cls._instances[key]
        
    async def acquire(self) -> None:
        """Wait for rate limit if needed."""
        if not self.rate_limit:
            return
            
        key = f"{self.namespace}:{self.rate_limit}"
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_times[key]
            if time_since_last < self.rate_limit:
                wait_time = self.rate_limit - time_since_last
                logger.debug(f"Rate limit hit for {self.namespace} - waiting {wait_time:.2f}s before next request")
                await asyncio.sleep(wait_time)
            self._last_request_times[key] = time.time()

class ProgressTracker:
    """Handles progress tracking and display."""
    def __init__(self, total: int, label: str = 'Processing'):
        self.total = total
        self.label = label
        self.current = 0
        self.current_item = ""
        
    def update(self, item: str = "") -> None:
        self.current += 1
        self.current_item = item
        
    @property
    def progress(self) -> float:
        return (self.current / self.total) * 100