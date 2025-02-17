from typing import Callable
from .providers.base import SearchProvider
from .providers.brave import BraveSearchProvider
from .providers.duckduckgo import DuckDuckGoSearchProvider
from .providers.oxylabs import OxylabsSearchProvider

ProviderCreator = Callable[[dict[str, str]], SearchProvider]

class SearchProviderFactory:
    _providers: dict[str, ProviderCreator] = {
        "brave": lambda creds: BraveSearchProvider(creds.get("BRAVE_API_KEY")),
        "oxylabs_google": lambda creds: OxylabsSearchProvider(
            creds.get("OXYLABS_USERNAME"),
            creds.get("OXYLABS_PASSWORD"),
            "google"
        ),
        "duckduckgo": lambda creds: DuckDuckGoSearchProvider(
            region=creds.get("DUCKDUCKGO_REGION"),
            safesearch=creds.get("DUCKDUCKGO_SAFESEARCH", "moderate")
        ),
        "oxylabs_bing": lambda creds: OxylabsSearchProvider(
            creds.get("OXYLABS_USERNAME"),
            creds.get("OXYLABS_PASSWORD"),
            "bing"
        )
    }
    
    @classmethod
    def create(cls, engine: str, credentials: dict[str, str]) -> SearchProvider:
        if engine not in cls._providers:
            raise ValueError(f"Unsupported search engine: {engine}")
            
        return cls._providers[engine](credentials)