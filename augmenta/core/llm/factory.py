from typing import Dict, Type
from .providers.base import LLMProvider
from .providers.openai import OpenAIProvider

class LLMFactory:
    """Factory for creating LLM provider instances"""
    
    _providers: Dict[str, Type[LLMProvider]] = {
        "openai": OpenAIProvider,
        # Add more providers here
    }
    
    @classmethod
    def create(cls, model: str) -> LLMProvider:
        """Create an LLM provider instance"""
        provider_name = model.split('/')[0].lower()
        
        if provider_name not in cls._providers:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
            
        provider_class = cls._providers[provider_name]
        return provider_class(model=model)