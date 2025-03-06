from typing import Dict, Type
from .base import SearchProvider
from .brave import BraveSearchProvider
from .oxylabs import OxylabsSearchProvider
from .google import GoogleSearchProvider
from .duckduckgo import DuckDuckGoSearchProvider

# Map of provider names to their classes
PROVIDERS: Dict[str, Type[SearchProvider]] = {
    "brave": BraveSearchProvider,
    "google": GoogleSearchProvider,
    "duckduckgo": DuckDuckGoSearchProvider,
    "oxylabs_google": OxylabsSearchProvider
}

def create_provider(name: str, credentials: Dict[str, str]) -> SearchProvider:
    """Create a provider instance with given credentials."""
    provider_class = PROVIDERS[name]
    return provider_class(credentials)

__all__ = [
    'SearchProvider',
    'BraveSearchProvider',
    'OxylabsSearchProvider',
    'GoogleSearchProvider',
    'DuckDuckGoSearchProvider',
    'PROVIDERS',
    'create_provider'
]