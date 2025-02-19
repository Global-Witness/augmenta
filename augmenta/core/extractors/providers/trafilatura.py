from typing import Optional
import logging
from trafilatura import extract
from trafilatura.settings import use_config
from .base import ContentProvider
from .http import HTTPProvider
from .playwright import PlaywrightProvider

logger = logging.getLogger(__name__)

class TrafilaturaProvider(ContentProvider):
    """Provider that extracts text using Trafilatura with fallback options."""
    
    def __init__(self):
        self.http_provider = HTTPProvider()
        self.playwright_provider = PlaywrightProvider()
        self.config = use_config()
        self.config.set("DEFAULT", "MIN_EXTRACTED_SIZE", "50")
        self.config.set("DEFAULT", "MIN_OUTPUT_SIZE", "50")
    
    async def get_content(self, url: str, timeout: int = 30) -> Optional[str]:
        """Attempt to fetch and extract content using available methods."""
        # Try HTTP first
        if content := await self.http_provider.get_content(url, timeout):
            if extracted := self._extract_text(content, url):
                return extracted
        
        # Fallback to Playwright
        logger.info(f"Falling back to Playwright for {url}")
        if content := await self.playwright_provider.get_content(url, timeout):
            return self._extract_text(content, url)
        
        return None
    
    def _extract_text(self, content: str, url: str) -> Optional[str]:
        """Extract text content using trafilatura."""
        try:
            extracted = extract(
                content,
                config=self.config,
                output_format="markdown",
                include_tables=True
            )
            
            return extracted if extracted and len(extracted) >= 50 else None
            
        except Exception as e:
            logger.error(f"Trafilatura extraction failed for {url}: {str(e)}")
            return None