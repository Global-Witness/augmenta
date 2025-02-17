import asyncio
from typing import Optional, Final
import logging
import aiohttp
from aiohttp import ClientTimeout, ClientError
from trafilatura import extract
from trafilatura.settings import use_config
from augmenta.utils.validators import is_valid_url
from .base import TextExtractor, ExtractionError

logger = logging.getLogger(__name__)

class TrafilaturaExtractor(TextExtractor):
    """Text extractor using Trafilatura library"""
    
    MAX_CONTENT_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
    MAX_RETRIES: Final[int] = 3
    RETRY_DELAY: Final[float] = 1.0
    USER_AGENT: Final[str] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
    
    def __init__(self) -> None:
        self.config = use_config()
        self.config.set("DEFAULT", "MIN_EXTRACTED_SIZE", "50")
        self.config.set("DEFAULT", "MIN_OUTPUT_SIZE", "50")
    
    async def extract(self, url: str, timeout: int = 30) -> Optional[str]:
        if not is_valid_url(url):
            logger.warning(f"Invalid URL format: {url}")
            return None
        
        timeout_settings = ClientTimeout(
            total=timeout,
            connect=timeout/3,
            sock_read=timeout
        )
        
        headers = {
            "User-Agent": self.USER_AGENT
        }
        
        for attempt in range(self.MAX_RETRIES):
            try:
                async with aiohttp.ClientSession(timeout=timeout_settings, headers=headers) as session:
                    async with session.get(url, allow_redirects=True, ssl=True) as response:
                        if response.status != 200:
                            logger.warning(f"HTTP {response.status} for {url}")
                            return None
                        
                        if not response.headers.get('content-type', '').startswith('text/'):
                            logger.warning(f"Unsupported content type for {url}")
                            return None
                        
                        content = await response.text()
                        if not content:
                            return None
                            
                        extracted = extract(
                            content,
                            config=self.config,
                            output_format="markdown",
                            include_tables=True
                        )
                        
                        return extracted if extracted and len(extracted) >= 50 else None
                        
            except ClientError as e:
                if attempt == self.MAX_RETRIES - 1:
                    logger.error(f"Network error for {url}: {str(e)}")
                    return None
                await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                
            except Exception as e:
                raise ExtractionError(
                    message=f"Extraction failed: {str(e)}",
                    url=url
                ) from e
        
        return None