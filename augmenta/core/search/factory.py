from typing import Callable, Dict, Any
from .providers.base import SearchProvider
from .providers.brave import BraveSearchProvider
from .providers.google import GoogleSearchProvider
from .providers.duckduckgo import DuckDuckGoSearchProvider
from .providers.oxylabs import OxylabsSearchProvider

ProviderCreator = Callable[[dict[str, str], Dict[str, Any]], SearchProvider]

class SearchProviderFactory:
    # Reserved keys that shouldn't be passed to the search provider
    _reserved_keys = {'engine', 'results'}
    
    _providers: dict[str, ProviderCreator] = {
        "brave": lambda creds, params: BraveSearchProvider(
            creds.get("BRAVE_API_KEY"),
            **params
        ),
        "google": lambda creds, params: GoogleSearchProvider(
            creds.get("GOOGLE_API_KEY"),
            creds.get("GOOGLE_CX"),
            **params
        ),
        "oxylabs_google": lambda creds, params: OxylabsSearchProvider(
            creds.get("OXYLABS_USERNAME"),
            creds.get("OXYLABS_PASSWORD"),
            "google",
            **params
        ),
        "duckduckgo": lambda creds, params: DuckDuckGoSearchProvider(
            region=creds.get("DUCKDUCKGO_REGION"),
            safesearch=creds.get("DUCKDUCKGO_SAFESEARCH", "moderate"),
            **params
        ),
        "oxylabs_bing": lambda creds, params: OxylabsSearchProvider(
            creds.get("OXYLABS_USERNAME"),
            creds.get("OXYLABS_PASSWORD"),
            "bing",
            **params
        )
    }
    
    @classmethod
    def create(cls, engine: str, credentials: dict[str, str], config: Dict[str, Any]) -> SearchProvider:
        if engine not in cls._providers:
            raise ValueError(f"Unsupported search engine: {engine}")
            
        # Filter out reserved keys from the config
        search_params = {k: v for k, v in config.items() if k not in cls._reserved_keys}
        
        return cls._providers[engine](credentials, search_params)