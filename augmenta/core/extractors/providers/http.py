import aiohttp
from typing import Optional, Final
from aiohttp import ClientTimeout, ClientError

# logging
import logging
import logfire
logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()])
logger = logging.getLogger(__name__)

class HTTPProvider:
    """Provider that fetches content using direct HTTP requests via aiohttp."""
    
    USER_AGENT: Final[str] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
    
    async def get_content(self, url: str, timeout: int = 30) -> Optional[str]:
        timeout_settings = ClientTimeout(
            total=timeout,
            connect=timeout/3,
            sock_read=timeout
        )
        
        headers = {
            "User-Agent": self.USER_AGENT
        }
        
        try:
            async with aiohttp.ClientSession(timeout=timeout_settings, headers=headers) as session:
                async with session.get(url, allow_redirects=True, ssl=True) as response:
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
                    
                    if not response.headers.get('content-type', '').startswith('text/'):
                        logger.warning(f"Unsupported content type for {url}")
                        return None
                    
                    content = await response.text()
                    return content if content else None
                    
        except ClientError as e:
            logger.error(f"Network error for {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {str(e)}")
            return None