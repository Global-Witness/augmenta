from abc import ABC, abstractmethod
from typing import Optional, Type, Any
from pydantic import BaseModel

class LLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    async def complete(
        self,
        prompt_system: str,
        prompt_user: str,
        response_format: Optional[Type[BaseModel]] = None
    ) -> Any:
        """Generate completion from the LLM"""
        pass