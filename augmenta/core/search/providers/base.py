from abc import ABC, abstractmethod
from typing import List

class SearchProvider(ABC):
    """Base class for search providers"""
    
    @abstractmethod
    async def search(self, query: str, results: int) -> List[str]:
        """Execute search and return list of URLs"""
        pass
        
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate that required credentials are available"""
        pass