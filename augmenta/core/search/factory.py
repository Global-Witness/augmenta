from typing import Dict, Type
from .providers.base import SearchProvider
from .providers.brave import BraveSearchProvider
from .providers.oxylabs import OxylabsSearchProvider

class SearchProviderFactory:
    """Factory for creating search provider instances"""
    
    _providers: Dict[str, Type[SearchProvider]] = {
        "brave": BraveSearchProvider,
        "oxylabs_google": lambda u, p: OxylabsSearchProvider(u, p, "google"),
        "oxylabs_bing": lambda u, p: OxylabsSearchProvider(u, p, "bing")
    }
    
    @classmethod
    def create(cls, engine: str, credentials: dict) -> SearchProvider:
        """Create a search provider instance"""
        if engine not in cls._providers:
            raise ValueError(f"Unsupported search engine: {engine}")
            
        provider_class = cls._providers[engine]
        
        if engine == "brave":
            provider = provider_class(credentials.get("BRAVE_API_KEY"))
        else:  # oxylabs
            provider = provider_class(
                credentials.get("OXYLABS_USERNAME"),
                credentials.get("OXYLABS_PASSWORD")
            )
            
        if not provider.validate_credentials():
            raise ValueError(f"Invalid credentials for {engine}")
            
        return provider