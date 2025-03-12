from typing import Optional
from trafilatura import extract
from trafilatura.settings import use_config

# logging
import logging
import logfire
logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()])
logger = logging.getLogger(__name__)

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