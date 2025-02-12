from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

@dataclass
class ExtractionError(Exception):
    """Base exception for extraction errors"""
    message: str
    url: Optional[str] = None
    
    def __str__(self) -> str:
        if self.url:
            return f"{self.message} (URL: {self.url})"
        return self.message

class TextExtractor(ABC):
    """Base class for text extractors"""
    
    @abstractmethod
    async def extract(self, url: str, timeout: int = 30) -> Optional[str]:
        """Extract text content from URL."""
        pass