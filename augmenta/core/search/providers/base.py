from abc import ABC, abstractmethod
from typing import List

class SearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str, results: int) -> List[str]:
        """Execute search and return list of result URLs."""
        pass