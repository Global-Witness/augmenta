from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class ProcessStatus:
    """
    Immutable data class representing process status information.
    
    Attributes:
        process_id: Unique identifier for the process
        config_hash: Hash of the configuration used
        start_time: When the process started
        last_updated: Time of last update
        status: Current status ('running', 'completed', 'failed')
        total_rows: Total number of rows to process
        processed_rows: Number of rows processed so far
    """
    process_id: str
    config_hash: str
    start_time: datetime
    last_updated: datetime
    status: str
    total_rows: int
    processed_rows: int

    def __post_init__(self) -> None:
        """Validate status values and row counts."""
        if self.status not in {'running', 'completed', 'failed'}:
            raise ValueError(f"Invalid status: {self.status}")
        if self.total_rows < 0:
            raise ValueError("Total rows cannot be negative")
        if self.processed_rows < 0:
            raise ValueError("Processed rows cannot be negative")
        if self.processed_rows > self.total_rows:
            raise ValueError("Processed rows cannot exceed total rows")

    @property
    def progress(self) -> float:
        """Calculate progress as a percentage."""
        return (self.processed_rows / self.total_rows * 100) if self.total_rows > 0 else 0

class CacheError(Exception):
    """Base exception for cache-related errors."""
    pass

class DatabaseError(CacheError):
    """Exception raised for database operation failures."""
    pass