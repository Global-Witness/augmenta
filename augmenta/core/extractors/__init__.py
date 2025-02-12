from typing import List, Tuple, Optional, Sequence
import concurrent.futures
import asyncio
import logging
from .base import TextExtractor, ExtractionError
from .trafilatura import TrafilaturaExtractor

logger = logging.getLogger(__name__)

async def extract_urls(
    urls: Sequence[str],
    max_workers: Optional[int] = 10,
    extractor: Optional[TextExtractor] = None,
    timeout: int = 30
) -> List[Tuple[str, Optional[str]]]:
    """Extract text from multiple URLs using parallel processing."""
    if not urls:
        return []
    
    extractor = extractor or TrafilaturaExtractor()
    max_workers = min(max_workers or 10, len(urls))
    
    async def extract_with_timeout(url: str) -> Tuple[str, Optional[str]]:
        try:
            text = await asyncio.wait_for(
                extractor.extract(url),
                timeout=timeout
            )
            return url, text
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Error processing {url}: {str(e)}")
            return url, None
    
    try:
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                loop.run_in_executor(
                    executor,
                    lambda u=url: asyncio.run(extract_with_timeout(u))
                )
                for url in urls
            ]
            
            results = await asyncio.gather(*futures)
            return list(results)
            
    except Exception as e:
        raise ExtractionError(f"Failed to process URLs: {str(e)}") from e

__all__ = ['TextExtractor', 'TrafilaturaExtractor', 'extract_urls', 'ExtractionError']