from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProcessStatus:
    """Data class for process status information"""
    process_id: str
    config_hash: str
    start_time: datetime
    last_updated: datetime
    status: str
    total_rows: int
    processed_rows: int

class CacheError(Exception):
    """Base exception for cache-related errors"""
    pass

class DatabaseError(CacheError):
    """Database operation related errors"""
    pass