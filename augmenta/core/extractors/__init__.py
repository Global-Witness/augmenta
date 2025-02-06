import concurrent.futures
import asyncio
from typing import List, Tuple, Optional
from .base import TextExtractor
from .trafilatura import TrafilaturaExtractor

async def extract_urls(
    urls: List[str],
    max_workers: int = 10,
    extractor: TextExtractor = None
) -> List[Tuple[str, Optional[str]]]:
    """Extract text from multiple URLs using parallel processing"""
    if not urls:
        return []
        
    extractor = extractor or TrafilaturaExtractor()
    
    # Use ThreadPoolExecutor for parallel processing
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            loop.run_in_executor(
                executor,
                lambda u: (u, asyncio.run(extractor.extract(u))),
                url
            )
            for url in urls
        ]
        
        results = await asyncio.gather(*futures)
        return results

__all__ = ['TextExtractor', 'TrafilaturaExtractor', 'extract_urls']