from abc import ABC, abstractmethod
from typing import Optional, Pattern
import re
from urllib.parse import urlparse
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
    
    # Common URL validation pattern
    URL_PATTERN: Pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    def validate_url(self, url: str) -> bool:
        """
        Validate URL format and accessibility.
        
        Args:
            url: URL string to validate
            
        Returns:
            bool: True if URL is valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
            
        url = url.strip()
        if not self.URL_PATTERN.match(url):
            return False
            
        try:
            result = urlparse(url)
            return all([
                result.scheme in ('http', 'https'),
                result.netloc,
                len(url) < 2048  # Common URL length limit
            ])
        except Exception:
            return False
    
    @abstractmethod
    async def extract(self, url: str, timeout: int = 30) -> Optional[str]:
        """
        Extract text content from URL.
        
        Args:
            url: URL to extract content from
            timeout: Timeout in seconds
            
        Returns:
            Optional[str]: Extracted text or None if extraction failed
            
        Raises:
            ExtractionError: If there's an error during extraction
        """
        pass