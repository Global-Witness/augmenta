from typing import Optional, Type
from pydantic import BaseModel
from .factory import LLMFactory
from .models import create_structure_class

async def make_request_llm(
    prompt_system: str,
    prompt_user: str,
    model: str = "openai/gpt-4-turbo-preview",
    response_format: Optional[Type[BaseModel]] = None
) -> str:
    """Make a request to an LLM"""
    provider = LLMFactory.create(model)
    return await provider.complete(prompt_system, prompt_user, response_format)

__all__ = ['make_request_llm', 'create_structure_class', 'LLMFactory']