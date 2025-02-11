"""Factory for creating and managing search provider instances."""

from typing import Dict, Type, Callable, Any
from .providers.base import SearchProvider
from .providers.brave import BraveSearchProvider
from .providers.oxylabs import OxylabsSearchProvider

ProviderCreator = Callable[[Any, Any], SearchProvider]

class SearchProviderFactory:
    """Factory for creating search provider instances with credential validation."""
    
    _providers: Dict[str, Type[SearchProvider] | ProviderCreator] = {
        "brave": BraveSearchProvider,
        "oxylabs_google": lambda u, p: OxylabsSearchProvider(u, p, "google"),
        "oxylabs_bing": lambda u, p: OxylabsSearchProvider(u, p, "bing")
    }
    
    @classmethod
    def create(cls, engine: str, credentials: dict[str, str]) -> SearchProvider:
        """
        Create and validate a search provider instance.
        
        Args:
            engine: Search engine identifier
            credentials: API credentials for the provider
            
        Returns:
            Configured search provider instance
            
        Raises:
            ValueError: If engine is unsupported or credentials are invalid
        """
        if engine not in cls._providers:
            raise ValueError(f"Unsupported search engine: {engine}")
            
        provider_class = cls._providers[engine]
        
        # Create provider instance based on engine type
        if engine == "brave":
            provider = provider_class(credentials.get("BRAVE_API_KEY"))
        else:  # oxylabs providers
            provider = provider_class(
                credentials.get("OXYLABS_USERNAME"),
                credentials.get("OXYLABS_PASSWORD")
            )
            
        if not provider.validate_credentials():
            raise ValueError(f"Invalid credentials for {engine}")
            
        return provider