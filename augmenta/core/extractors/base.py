from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urlparse

class TextExtractor(ABC):
    """Base class for text extractors"""
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format"""
        if not url or not url.strip():
            return False
            
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @abstractmethod
    async def extract(self, url: str, timeout: int = 30) -> Optional[str]:
        """Extract text content from URL"""
        pass