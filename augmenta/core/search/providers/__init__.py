from .base import SearchProvider
from .brave import BraveSearchProvider
from .google import GoogleSearchProvider
from .oxylabs import OxylabsSearchProvider
from .duckduckgo import DuckDuckGoSearchProvider

__all__ = [
    'SearchProvider',
    'BraveSearchProvider', 
    'GoogleSearchProvider',
    'DuckDuckGoSearchProvider', 
    'OxylabsSearchProvider'
]