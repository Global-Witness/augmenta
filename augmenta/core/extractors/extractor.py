from typing import Optional
import logging
from abc import ABC, abstractmethod
from augmenta.utils.validators import is_valid_url
from .providers import ExtractionError, ContentProvider

logger = logging.getLogger(__name__)

class TextExtractor(ABC):
    """Base class for text extractors"""
    
    def __init__(self, provider: ContentProvider) -> None:
        self.provider = provider
    
    @abstractmethod
    async def extract(self, url: str, timeout: int = 30) -> Optional[str]:
        """Extract text content from URL."""
        pass

class DefaultTextExtractor(TextExtractor):
    """Default implementation of TextExtractor"""
    
    async def extract(self, url: str, timeout: int = 30) -> Optional[str]:
        """Extract text content from URL using the configured provider."""
        if not is_valid_url(url):
            logger.warning(f"Invalid URL format: {url}")
            return None
        
        try:
            return await self.provider.get_content(url, timeout)
        except Exception as e:
            raise ExtractionError(
                message=f"Extraction failed: {str(e)}",
                url=url
            ) from e