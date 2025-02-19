from typing import Optional, Type
import logging
from .extractor import DefaultTextExtractor, TextExtractor
from .providers import TrafilaturaProvider, ContentProvider

logger = logging.getLogger(__name__)

def create_extractor(
    provider_class: Optional[Type[ContentProvider]] = None
) -> TextExtractor:
    """
    Factory function to create a TextExtractor instance with the specified provider.
    
    Args:
        provider_class: Optional provider class to use. Defaults to TrafilaturaProvider.
        
    Returns:
        TextExtractor: Configured extractor instance
    """
    provider = (provider_class or TrafilaturaProvider)()
    return DefaultTextExtractor(provider)