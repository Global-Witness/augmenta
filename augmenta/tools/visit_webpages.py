from typing import List, Tuple, Dict, Optional
from markitdown import MarkItDown
import asyncio

# logging
import logging
import logfire
logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()])
logger = logging.getLogger(__name__)

async def visit_webpages(urls: List[str], max_workers: int = 10, timeout: int = 30) -> List[Dict[str, str]]:
    """Implementation of webpage content extraction.
    
    Args:
        urls: List of URLs to process
        max_workers: Maximum number of concurrent workers
        timeout: Timeout in seconds for each request
        
    Returns:
        List of dictionaries containing 'url' and 'content' fields
    """
    md = MarkItDown(enable_plugins=False)  # Create single instance

    async def process_url(url: str) -> Dict[str, str]:
        try:
            # Convert content using markitdown
            converted = md.convert(url)
            
            return {
                "url": url,
                "content": converted.text_content if converted else ""
            }
            
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            return {"url": url, "content": "Couldn't extract content"}

    # Process URLs concurrently with a limit on max workers
    semaphore = asyncio.Semaphore(max_workers)
    
    async def process_with_semaphore(url: str) -> Tuple[str, Optional[str]]:
        async with semaphore:
            return await process_url(url)

    tasks = [process_with_semaphore(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results