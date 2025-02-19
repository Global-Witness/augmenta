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

class ContentProvider(ABC):
    """Base class for content providers that fetch and process content."""
    
    @abstractmethod
    async def get_content(self, url: str, timeout: int = 30) -> Optional[str]:
        """
        Fetch and process content from a URL.
        
        Args:
            url: The URL to fetch content from
            timeout: Timeout in seconds
            
        Returns:
            Optional[str]: Processed content if successful, None otherwise
        """
        pass