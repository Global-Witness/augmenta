from typing import Optional, Type
from pydantic import BaseModel
from .provider import LLMProvider
from .models import create_structure_class

async def make_request_llm(
    prompt_system: str,
    prompt_user: str,
    model: str = "openai/gpt-4o-mini",
    response_format: Optional[Type[BaseModel]] = None
) -> str:
    """Make a request to an LLM"""
    provider = LLMProvider(model)
    return await provider.complete(prompt_system, prompt_user, response_format)

__all__ = ['make_request_llm', 'create_structure_class', 'LLMProvider']