"""Base interface for search provider implementations."""

from abc import ABC, abstractmethod
from typing import List

class SearchProvider(ABC):
    """Abstract base class defining the interface for search providers."""
    
    @abstractmethod
    async def search(self, query: str, results: int) -> List[str]:
        """
        Execute search and return list of URLs.
        
        Args:
            query: Search query string
            results: Number of results to return
            
        Returns:
            List of URLs from search results
        """
        pass
        
    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate that required credentials are available and valid.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        pass