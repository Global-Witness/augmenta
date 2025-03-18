import httpx
from typing import Optional, Final
from httpx import TimeoutException, RequestError

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