"""
Module for extracting text content from URLs using asynchronous HTTP requests.
Provides functionality for single and batch URL text extraction.
"""

from typing import List, Tuple, Optional
import logging
from urllib.parse import urlparse

import asyncio
import aiohttp
from aiohttp import ClientTimeout
from trafilatura import extract

logger = logging.getLogger(__name__)

async def extract_url(url: str, timeout: int = 30) -> Optional[str]:
    """
    Extract text content from a URL asynchronously.
    
    Args:
        url (str): URL to extract text from
        timeout (int): Request timeout in seconds
        
    Returns:
        Optional[str]: Extracted text in markdown format, or None if extraction failed
    
    Raises:
        ValueError: If URL is malformed or empty
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    
    # Validate URL format
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL format")
    except Exception as e:
        logger.error(f"URL validation failed for {url}: {str(e)}")
        return None

    try:
        timeout_settings = ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=timeout_settings) as session:
            async with session.get(url, allow_redirects=True) as response:
                if response.status == 200:
                    content = await response.text()
                    extracted_text = extract(content, output_format="markdown")
                    return extracted_text if extracted_text else None
                
                logger.warning(f"Failed to fetch {url}. Status: {response.status}")
                return None
                
    except aiohttp.ClientError as e:
        logger.error(f"Network error for {url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing {url}: {str(e)}")
        return None

async def extract_urls(urls: List[str]) -> List[Tuple[str, Optional[str]]]:
    """
    Extract text from multiple URLs asynchronously.
    
    Args:
        urls (List[str]): List of URLs to extract text from
        
    Returns:
        List[Tuple[str, Optional[str]]]: List of tuples containing (url, extracted_text)
    
    Raises:
        ValueError: If URLs list is empty
    """
    if not urls:
        raise ValueError("URLs list cannot be empty")

    tasks = [extract_url(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and pair results with URLs
    return [(url, result if not isinstance(result, Exception) else None) 
            for url, result in zip(urls, results)]