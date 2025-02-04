from trafilatura import extract
from typing import List, Tuple, Optional
import aiohttp
import asyncio

async def extract_url(source: str) -> Optional[str]:
    """
    Extract text content from a URL asynchronously.
    
    Args:
        source (str): URL to extract text from
        
    Returns:
        Optional[str]: Extracted text in markdown format, or None if extraction failed
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(source) as response:
                if response.status == 200:
                    content = await response.text()
                    result = extract(content, output_format="markdown")
                    return result
                return None
    except Exception:
        return None

async def extract_urls(urls: List[str]) -> List[Tuple[str, Optional[str]]]:
    """
    Extract text from multiple URLs asynchronously.
    
    Args:
        urls (List[str]): List of URLs to extract text from
        
    Returns:
        List[Tuple[str, Optional[str]]]: List of tuples containing (url, extracted_text)
    """
    tasks = [extract_url(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return list(zip(urls, results))