"""
Data models and exceptions for the cache system.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

ProcessStatusType = Literal['running', 'completed', 'failed']

class CacheError(Exception):
    """Base exception for cache-related errors."""
    pass

class DatabaseError(CacheError):
    """Exception raised for database operation failures."""
    pass

class ValidationError(CacheError):
    """Exception raised for data validation failures."""
    pass

@dataclass(frozen=True)
class ProcessStatus:
    """
    Immutable data class representing process status information.
    """
    process_id: str
    config_hash: str
    start_time: datetime
    last_updated: datetime
    status: ProcessStatusType
    total_rows: int
    processed_rows: int

    def __post_init__(self) -> None:
        """Validate status values and row counts."""
        if not isinstance(self.process_id, str) or not self.process_id.strip():
            raise ValidationError("Process ID must be a non-empty string")
            
        if not isinstance(self.config_hash, str) or not self.config_hash.strip():
            raise ValidationError("Config hash must be a non-empty string")
            
        if not isinstance(self.start_time, datetime):
            raise ValidationError("Start time must be a datetime object")
            
        if not isinstance(self.last_updated, datetime):
            raise ValidationError("Last updated must be a datetime object")
            
        if self.status not in {'running', 'completed', 'failed'}:
            raise ValidationError(f"Invalid status: {self.status}")
            
        if not isinstance(self.total_rows, int) or self.total_rows < 0:
            raise ValidationError("Total rows must be a non-negative integer")
            
        if not isinstance(self.processed_rows, int) or self.processed_rows < 0:
            raise ValidationError("Processed rows must be a non-negative integer")
            
        if self.processed_rows > self.total_rows:
            raise ValidationError("Processed rows cannot exceed total rows")
            
        if self.last_updated < self.start_time:
            raise ValidationError("Last updated cannot be before start time")

    @property
    def progress(self) -> float:
        """Calculate progress as a percentage."""
        return (self.processed_rows / self.total_rows * 100) if self.total_rows > 0 else 0.0

    @property
    def duration(self) -> timedelta:
        """Calculate process duration."""
        return self.last_updated - self.start_time