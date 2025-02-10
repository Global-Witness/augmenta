from typing import Optional
import logging
import aiohttp
from aiohttp import ClientTimeout
from trafilatura import extract
from .base import TextExtractor

logger = logging.getLogger(__name__)

class TrafilaturaExtractor(TextExtractor):
    """Text extractor using Trafilatura"""
    
    async def extract(self, url: str, timeout: int = 30) -> Optional[str]:
        """Extract text content from URL using Trafilatura"""
        if not self.validate_url(url):
            return None
            
        try:
            timeout_settings = ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_settings) as session:
                async with session.get(url, allow_redirects=True) as response:
                    if response.status == 200:
                        content = await response.text()
                        return extract(content, output_format="markdown")
            return None
                
        except Exception as e:
            # Changed to debug level since this is expected behavior
            logger.debug(f"Could not extract content from {url}: {str(e)}")
            return None