import httpx
from typing import Optional, Final, List, Tuple, Dict
from httpx import TimeoutException, RequestError
from trafilatura import extract
from trafilatura.settings import use_config
import asyncio
from concurrent.futures import ThreadPoolExecutor

# logging
import logging
import logfire
logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()])
logger = logging.getLogger(__name__)

class HTTPProvider:
    """Provider that fetches content using direct HTTP requests via httpx."""
    
    USER_AGENT: Final[str] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
    
    async def get_content(self, url: str, timeout: int = 30) -> Optional[str]:
        # Configure timeouts similar to aiohttp's ClientTimeout
        timeout_settings = httpx.Timeout(
            timeout=timeout,
            connect=timeout/3,
            read=timeout
        )
        
        headers = {
            "User-Agent": self.USER_AGENT
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout_settings, headers=headers) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                
                if response.status_code != 200:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    return None
                
                if not response.headers.get('content-type', '').startswith('text/'):
                    logger.warning(f"Unsupported content type for {url}")
                    return None
                
                content = response.text
                return content if content else None
                
        except TimeoutException as e:
            logger.error(f"Timeout error for {url}: {str(e)}")
            return None
        except RequestError as e:
            logger.error(f"Network error for {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {str(e)}")
            return None

class TrafilaturaProvider:
    """Provider that extracts text content using Trafilatura."""
    
    def __init__(self):
        self.config = use_config()
        self.config.set("DEFAULT", "MIN_EXTRACTED_SIZE", "50")
        self.config.set("DEFAULT", "MIN_OUTPUT_SIZE", "50")
    
    async def get_content(self, html_content: str, timeout: int = 30) -> Optional[str]:
        """Extract text content from HTML using trafilatura.
        
        Args:
            html_content: The HTML content to extract text from
            timeout: Not used, kept for interface consistency
            
        Returns:
            Optional[str]: Extracted markdown text if successful, None otherwise
        """
        try:
            extracted = extract(
                html_content,
                config=self.config,
                output_format="markdown",
                include_tables=True
            )
            
            return extracted if extracted and len(extracted) >= 50 else None
            
        except Exception as e:
            logger.error(f"Trafilatura extraction failed: {str(e)}")
            return None

async def visit_webpages(urls: List[str], max_workers: int = 10, timeout: int = 30) -> List[Dict[str, str]]:
    """Implementation of webpage content extraction.
    
    Args:
        urls: List of URLs to process
        max_workers: Maximum number of concurrent workers
        timeout: Timeout in seconds for each request
        
    Returns:
        List of dictionaries containing 'url' and 'content' fields
    """
    http_provider = HTTPProvider()
    trafilatura_provider = TrafilaturaProvider()

    async def process_url(url: str) -> Dict[str, str]:
        try:
            # First get HTML content
            html_content = await http_provider.get_content(url, timeout)
            if not html_content:
                return {"url": url, "content": ""}
                
            # Then extract meaningful content from HTML
            extracted = await trafilatura_provider.get_content(html_content, timeout)
            return {
                "url": url,
                "content": extracted if extracted else ""
            }
            
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            return {"url": url, "content": ""}

    # Process URLs concurrently with a limit on max workers
    semaphore = asyncio.Semaphore(max_workers)
    
    async def process_with_semaphore(url: str) -> Tuple[str, Optional[str]]:
        async with semaphore:
            return await process_url(url)

    tasks = [process_with_semaphore(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results