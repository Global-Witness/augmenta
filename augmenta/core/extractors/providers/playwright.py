import asyncio
from typing import Optional
import sys
import subprocess
from playwright.async_api import (
    async_playwright, 
    TimeoutError as PlaywrightTimeout,
    Error as PlaywrightError,
    Page,
    Browser,
    BrowserContext
)

# logging
import logging
import logfire
logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()])
logger = logging.getLogger(__name__)

class PlaywrightProvider:
    """Provider that fetches content using Playwright browser automation."""
    
    _browser_installed = False
    
    @classmethod
    async def ensure_browser_installed(cls) -> None:
        """Ensure Chromium browser is installed. Thread-safe and idempotent."""
        if cls._browser_installed:
            return
            
        try:
            # Check if browser is already installed by trying to launch it
            async with async_playwright() as p:
                await p.chromium.launch()
                cls._browser_installed = True
                return
        except PlaywrightError as e:
            if "Browser is not installed" not in str(e):
                raise
            
        logger.info("Installing Chromium browser for Playwright...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            cls._browser_installed = True
            logger.info("Chromium browser installation completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Playwright browser: {e}")
            raise
    
    async def get_content(self, url: str, timeout: int = 30) -> Optional[str]:
        # Ensure browser is installed before first use
        await self.ensure_browser_installed()
        
        browser = None
        context = None
        page = None
        
        try:
            logger.debug(f"Initializing Playwright for {url}")
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=IsolateOrigins,site-per-process',
                    ]
                )
                logger.debug(f"Browser launched for {url}")
                
                context = await self._create_context(browser)
                logger.debug(f"Browser context created for {url}")
                
                page = await context.new_page()
                logger.debug(f"New page created for {url}")
                
                # Create a task for content extraction
                content_task = asyncio.create_task(
                    self._navigate_and_get_content(page, url, timeout)
                )
                
                try:
                    return await content_task
                except asyncio.CancelledError:
                    logger.error(f"Content extraction cancelled for {url}")
                    # Ensure task is properly cleaned up
                    if not content_task.done():
                        content_task.cancel()
                    return None
                
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
            logger.debug(f"Starting cleanup for {url}")
            # Clean up resources in reverse order with individual try/except blocks
            cleanup_timeout = 5  # 5 seconds timeout for cleanup operations
            
            if page:
                try:
                    logger.debug(f"Closing page for {url}")
                    await asyncio.wait_for(page.close(), timeout=cleanup_timeout)
                except asyncio.TimeoutError:
                    logger.error(f"Timeout while closing page for {url}")
                except Exception as e:
                    logger.debug(f"Error closing page: {str(e)}")
            
            if context:
                try:
                    logger.debug(f"Closing context for {url}")
                    await asyncio.wait_for(context.close(), timeout=cleanup_timeout)
                except asyncio.TimeoutError:
                    logger.error(f"Timeout while closing context for {url}")
                except Exception as e:
                    logger.debug(f"Error closing context: {str(e)}")
            
            if browser:
                try:
                    logger.debug(f"Closing browser for {url}")
                    await asyncio.wait_for(browser.close(), timeout=cleanup_timeout)
                except asyncio.TimeoutError:
                    logger.error(f"Timeout while closing browser for {url}")
                except Exception as e:
                    logger.debug(f"Error closing browser: {str(e)}")
                    
            logger.debug(f"Cleanup completed for {url}")

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
            logger.debug(f"Starting navigation to {url}")
            # Set shorter timeout for initial navigation
            navigation_timeout = min(timeout * 1000, 30000)  # max 30 seconds
            
            # Navigate with more robust error handling
            response = await page.goto(
                url,
                timeout=navigation_timeout,
                wait_until='domcontentloaded'  # Less strict than 'networkidle'
            )
            logger.debug(f"Navigation completed for {url}")
            
            if not response:
                logger.warning(f"No response received for {url}")
                return None
                
            if response.status >= 400:
                logger.warning(f"HTTP {response.status} for {url}")
                return None
            
            # Wait for network to be relatively idle
            try:
                logger.debug(f"Waiting for network idle state for {url}")
                await page.wait_for_load_state('networkidle', timeout=5000)
                logger.debug(f"Network idle state reached for {url}")
            except PlaywrightTimeout:
                logger.info(f"Network idle timeout for {url} - proceeding anyway")
            
            # Check current URL for redirects to login pages
            current_url = page.url.lower()
            if any(text in current_url for text in ['login', 'signin', 'auth']):
                logger.warning(f"Redirected to login page: {current_url}")
                return None
            
            try:
                logger.debug(f"Starting content extraction for {url}")
                # Get the page content with explicit timeout
                content = await asyncio.wait_for(
                    page.content(),
                    timeout=timeout
                )
                logger.debug(f"Content extraction completed for {url}")
                
                if not content or len(content.strip()) < 100:  # Minimum content length
                    logger.warning(f"Retrieved insufficient content for {url}")
                    return None
                    
                return content
            except asyncio.TimeoutError:
                logger.error(f"Content extraction timed out for {url}")
                return None
            
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