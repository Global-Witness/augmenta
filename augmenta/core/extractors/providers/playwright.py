import logging
from typing import Optional
from playwright.async_api import (
    async_playwright, 
    TimeoutError as PlaywrightTimeout,
    Error as PlaywrightError,
    Page,
    Browser,
    BrowserContext
)
from .base import ContentProvider

logger = logging.getLogger(__name__)

class PlaywrightProvider(ContentProvider):
    """Provider that fetches content using Playwright browser automation."""
    
    async def get_content(self, url: str, timeout: int = 30) -> Optional[str]:
        browser = None
        context = None
        page = None
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=IsolateOrigins,site-per-process',
                    ]
                )
                
                context = await self._create_context(browser)
                page = await context.new_page()
                
                return await self._navigate_and_get_content(page, url, timeout)
                
        except PlaywrightTimeout:
            logger.error(f"Playwright timeout for {url}")
            return None
        except PlaywrightError as e:
            logger.error(f"Playwright error for {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {str(e)}")
            return None
        finally:
            # Clean up resources in reverse order
            try:
                if page:
                    await page.close()
                if context:
                    await context.close()
                if browser:
                    await browser.close()
            except Exception as e:
                logger.warning(f"Error during Playwright cleanup: {str(e)}")
    
    async def _create_context(self, browser: Browser) -> BrowserContext:
        """Create a new browser context with specific settings."""
        return await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
        )
    
    async def _navigate_and_get_content(
        self, 
        page: Page, 
        url: str, 
        timeout: int
    ) -> Optional[str]:
        """Handle page navigation and content extraction."""
        try:
            # Set shorter timeout for initial navigation
            navigation_timeout = min(timeout * 1000, 30000)  # max 30 seconds
            
            # Navigate with more robust error handling
            response = await page.goto(
                url,
                timeout=navigation_timeout,
                wait_until='domcontentloaded'  # Less strict than 'networkidle'
            )
            
            if not response:
                logger.warning(f"No response received for {url}")
                return None
                
            if response.status >= 400:
                logger.warning(f"HTTP {response.status} for {url}")
                return None
            
            # Wait for network to be relatively idle
            try:
                await page.wait_for_load_state('networkidle', timeout=5000)
            except PlaywrightTimeout:
                logger.info(f"Network idle timeout for {url} - proceeding anyway")
            
            # Check current URL for redirects to login pages
            current_url = page.url.lower()
            if any(text in current_url for text in ['login', 'signin', 'auth']):
                logger.warning(f"Redirected to login page: {current_url}")
                return None
            
            # Get the page content
            content = await page.content()
            if not content or len(content.strip()) < 100:  # Minimum content length
                logger.warning(f"Retrieved insufficient content for {url}")
                return None
                
            return content
            
        except PlaywrightTimeout:
            logger.error(f"Navigation timeout for {url}")
            return None
        except PlaywrightError as e:
            if 'ERR_ABORTED' in str(e):
                logger.error(f"Page load aborted for {url}: {str(e)}")
            elif 'Target closed' in str(e):
                logger.error(f"Target closed while loading {url}: {str(e)}")
            else:
                logger.error(f"Playwright error for {url}: {str(e)}")
            return None