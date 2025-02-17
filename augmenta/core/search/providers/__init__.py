from .base import SearchProvider
from .brave import BraveSearchProvider
from .oxylabs import OxylabsSearchProvider
from .duckduckgo import DuckDuckGoSearchProvider

__all__ = [
    'SearchProvider',
    'BraveSearchProvider', 
    'OxylabsSearchProvider',
    'DuckDuckGoSearchProvider'
]