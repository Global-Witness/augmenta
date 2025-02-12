"""Data models for the cache system."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from augmenta.utils.validators import validate_string, validate_int, validate_datetime
from augmenta.utils.exceptions import ValidationError

ProcessStatusType = Literal['running', 'completed', 'failed']

@dataclass(frozen=True)
class ProcessStatus:
    """Immutable data class representing process status information."""
    process_id: str
    config_hash: str
    start_time: datetime
    last_updated: datetime
    status: ProcessStatusType
    total_rows: int
    processed_rows: int

    def __post_init__(self) -> None:
        """Validate status values."""
        validate_string(self.process_id, "Process ID")
        validate_string(self.config_hash, "Config hash")
        validate_datetime(self.start_time, "Start time")
        validate_datetime(self.last_updated, "Last updated")
        validate_int(self.total_rows, "Total rows")
        validate_int(self.processed_rows, "Processed rows")
        
        if self.status not in {'running', 'completed', 'failed'}:
            raise ValidationError(f"Invalid status: {self.status}")
            
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