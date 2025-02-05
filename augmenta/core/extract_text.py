"""
Module for extracting text content from URLs using asynchronous HTTP requests.
Provides functionality for single and batch URL text extraction with parallel processing.
"""

from typing import List, Tuple, Optional
import logging
from urllib.parse import urlparse
import concurrent.futures
import urllib3
import warnings

import asyncio
import aiohttp
from aiohttp import ClientTimeout
from trafilatura import extract
from trafilatura.downloads import fetch_url

# Configure logging to be less verbose
logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)
logging.getLogger('charset_normalizer').setLevel(logging.ERROR)

# Completely disable trafilatura's download errors
trafilatura_logger = logging.getLogger('trafilatura.downloads')
trafilatura_logger.setLevel(logging.CRITICAL)
trafilatura_logger.propagate = False

# Suppress specific warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning, module='charset_normalizer')

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Suppress specific warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning, module='charset_normalizer')

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

def is_common_connection_error(e: Exception) -> bool:
    """
    Check if an exception is a common connection error that shouldn't be logged.
    
    Args:
        e (Exception): The exception to check
        
    Returns:
        bool: True if it's a common connection error, False otherwise
    """
    error_str = str(e).lower()
    common_errors = [
        'connection aborted',
        'connection refused',
        'connection reset',
        'remote end closed connection',
        'max retries exceeded',
        'timeout',
        'ssl',
        'certificate',
        'too many redirects',
        '[errno'
    ]
    return any(err in error_str for err in common_errors)

async def extract_url(url: str, timeout: int = 30) -> Optional[str]:
    """
    Extract text content from a URL asynchronously.
    
    Args:
        url (str): URL to extract text from
        timeout (int): Request timeout in seconds
        
    Returns:
        Optional[str]: Extracted text in markdown format, or None if extraction failed
    """
    if not url or not url.strip():
        return None
    
    # Validate URL format
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return None
    except Exception:
        return None

    try:
        timeout_settings = ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=timeout_settings) as session:
            async with session.get(url, allow_redirects=True) as response:
                if response.status == 200:
                    content = await response.text()
                    extracted_text = extract(content, output_format="markdown")
                    return extracted_text if extracted_text else None
                return None
                
    except Exception as e:
        if not is_common_connection_error(e):
            logger.error(f"Unexpected error processing {url}: {str(e)}")
        return None

def extract_url_sync(url: str) -> Tuple[str, Optional[str]]:
    """
    Synchronous version of extract_url for use with ThreadPoolExecutor.
    
    Args:
        url (str): URL to extract text from
        
    Returns:
        Tuple[str, Optional[str]]: Tuple of (url, extracted_text)
    """
    try:
        downloaded = fetch_url(url)
        if downloaded:
            extracted_text = extract(downloaded, output_format="markdown")
            return url, extracted_text if extracted_text else None
        return url, None
    except Exception as e:
        if not is_common_connection_error(e):
            logger.error(f"Error extracting {url}: {str(e)}")
        return url, None

async def extract_urls(urls: List[str], max_workers: int = 10) -> List[Tuple[str, Optional[str]]]:
    """
    Extract text from multiple URLs using parallel processing.
    
    Args:
        urls (List[str]): List of URLs to extract text from
        max_workers (int): Maximum number of parallel workers
        
    Returns:
        List[Tuple[str, Optional[str]]]: List of tuples containing (url, extracted_text)
    """
    if not urls:
        return []

    # Use ThreadPoolExecutor for parallel processing
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all URLs to the executor
        futures = [
            loop.run_in_executor(executor, extract_url_sync, url)
            for url in urls
        ]
        
        # Wait for all futures to complete
        results = await asyncio.gather(*futures)
        
        return results