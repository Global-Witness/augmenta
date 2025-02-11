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
    """
    Extract text from multiple URLs using parallel processing.
    
    Args:
        urls: Sequence of URLs to process
        max_workers: Maximum number of concurrent workers
        extractor: Custom extractor instance (defaults to TrafilaturaExtractor)
        timeout: Timeout in seconds for each extraction
        
    Returns:
        List of tuples containing (url, extracted_text)
        
    Raises:
        ExtractionError: If there's a critical error during extraction
    """
    if not urls:
        return []
    
    extractor = extractor or TrafilaturaExtractor()
    max_workers = min(max_workers or 10, len(urls))  # Optimize worker count
    
    async def extract_with_timeout(url: str) -> Tuple[str, Optional[str]]:
        try:
            text = await asyncio.wait_for(
                extractor.extract(url),
                timeout=timeout
            )
            return url, text
        except asyncio.TimeoutError:
            logger.warning(f"Timeout while processing {url}")
            return url, None
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
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