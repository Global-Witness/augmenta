from typing import List, Optional, Sequence, Protocol
import asyncio
import logging
from dataclasses import dataclass

from augmenta.utils.validators import is_valid_url

logger = logging.getLogger(__name__)

# Default configuration for AI agent use
DEFAULT_MAX_WORKERS = 10
DEFAULT_TIMEOUT = 30

@dataclass
class ExtractionError(Exception):
    """Base exception for extraction errors"""
    message: str
    url: Optional[str] = None
    
    def __str__(self) -> str:
        if self.url:
            return f"{self.message} (URL: {self.url})"
        return self.message

class ContentProvider(Protocol):
    """Protocol for content providers that fetch and process content."""
    async def get_content(self, url: str, timeout: int = 30) -> Optional[str]:
        """Fetch and process content from a URL."""
        ...

# Configure providers as module-level instances
from .providers import HTTPProvider, PlaywrightProvider, TrafilaturaProvider

http_provider = HTTPProvider()
playwright_provider = PlaywrightProvider()
text_provider = TrafilaturaProvider()

async def _visit_webpage_impl(url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[str]:
    """Internal implementation of webpage visiting with full configuration."""
    if not is_valid_url(url):
        logger.warning(f"Invalid URL format: {url}")
        return None
    
    try:
        # First try with HTTP provider
        content = await http_provider.get_content(url, timeout)
        if not content:
            # Fallback to Playwright if HTTP fails
            logger.debug(f"HTTP extraction failed for {url}, trying Playwright")
            content = await playwright_provider.get_content(url, timeout)
        
        if content:
            # Extract main text using trafilatura
            return await text_provider.get_content(content)
        
        return None
    
    except Exception as e:
        raise ExtractionError(
            message=f"Extraction failed: {str(e)}",
            url=url
        ) from e

async def _visit_webpages_impl(
    urls: Sequence[str],
    max_workers: int = DEFAULT_MAX_WORKERS,
    timeout: int = DEFAULT_TIMEOUT
) -> List[tuple[str, Optional[str]]]:
    """Internal implementation of multiple webpage visits with full configuration."""
    if not urls:
        return []
    
    max_workers = min(max_workers, len(urls))
    
    async def process_url(url: str) -> tuple[str, Optional[str]]:
        try:
            text = await asyncio.wait_for(
                _visit_webpage_impl(url),
                timeout=timeout
            )
            return url, text
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Error processing {url}: {str(e)}")
            return url, None
    
    try:
        tasks = [process_url(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return list(results)
    except Exception as e:
        raise ExtractionError(f"Failed to process URLs: {str(e)}")

# AI agent interface
async def visit_webpages(urls: Sequence[str]) -> str:
    """Visit webpages and extract their main content as markdown.
    
    This function processes multiple URLs and attempts to extract their main content
    using HTTP requests first, falling back to browser automation if needed. The
    extracted HTML is then converted to markdown format.
    
    Args:
        urls: A sequence of URLs to process
        
    Returns:
        A markdown formatted string containing the extracted content from each URL,
        with headers and separators between different sources.
        
    Example:
        >>> urls = ["https://example.com", "https://example.org"]
        >>> results = await visit_webpages(urls)
        >>> print(results)
        # Content from https://example.com
        
        Main content: here...
        
        ---
        # Content from https://example.org
        
        More content here...
    """
    results = await _visit_webpages_impl(
        urls=urls,
        max_workers=DEFAULT_MAX_WORKERS,
        timeout=DEFAULT_TIMEOUT
    )
    
    # Format results as markdown
    formatted_sections = []
    for url, content in results:
        if content:
            formatted_sections.extend([
                f"# Content from {url}",
                "",
                content.strip(),
                "",
                "---"
            ])
    
    return "\n".join(formatted_sections[:-1] if formatted_sections else ["No content extracted"])

__all__ = ['visit_webpages', 'ExtractionError']