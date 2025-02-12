"""Utility functions and classes for the Augmenta package."""

import json
import hashlib
import asyncio
import time
from pathlib import Path
from typing import Dict, Optional, ClassVar, Union
from dataclasses import dataclass

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
        if not self.rate_limit:
            return
            
        async with self._lock:
            time_since_last = time.time() - self._last_request_time
            if time_since_last < self.rate_limit:
                await asyncio.sleep(self.rate_limit - time_since_last)
            self._last_request_time = time.time()

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