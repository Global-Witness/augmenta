from typing import List, Tuple, Optional, Sequence
import asyncio
import logging
from .extractor import TextExtractor, DefaultTextExtractor
from .providers import ExtractionError
from .factory import create_extractor

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
    
    extractor = extractor or create_extractor()
    max_workers = min(max_workers or 10, len(urls))
    
    async def extract_single(url: str) -> Tuple[str, Optional[str]]:
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
        tasks = [extract_single(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return list(results)
    except Exception as e:
        raise ExtractionError(f"Failed to process URLs: {str(e)}") from e

__all__ = ['TextExtractor', 'DefaultTextExtractor', 'create_extractor', 'extract_urls', 'ExtractionError']