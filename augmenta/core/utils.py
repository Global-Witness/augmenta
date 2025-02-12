"""
Utility functions and classes for the Augmenta package.
"""

import json
import hashlib
import asyncio
import time
from pathlib import Path
from typing import Dict, Optional, ClassVar, Union
from dataclasses import dataclass

def get_hash(data: Union[dict, Path, str], chunk_size: int = 8192) -> str:
    """
    Generate a deterministic hash of data or file contents.
    
    Args:
        data: Data to hash - can be a dictionary, Path object, or string filepath
        chunk_size: Size of chunks to read when processing files (bytes)
        
    Returns:
        str: SHA-256 hash of the data
        
    Raises:
        TypeError: If data is not a dictionary, Path, or string
        FileNotFoundError: If file path does not exist
    """
    hasher = hashlib.sha256()
    
    if isinstance(data, dict):
        # For dictionaries, hash the sorted JSON representation
        hasher.update(json.dumps(data, sort_keys=True).encode('utf-8'))
    elif isinstance(data, (str, Path)):
        # For files, hash the contents in chunks
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