from typing import Optional, Type, Union
from pydantic import BaseModel
from .provider import LLMProvider
from .models import create_structure_class
from ..utils import RateLimiter

# Create a single global rate limiter instance
_rate_limiter = None

async def make_request_llm(
    prompt_system: str,
    prompt_user: str,
    model: str,
    response_format: Optional[Type[BaseModel]] = None,
    rate_limit: Optional[float] = None
) -> Union[str, dict, BaseModel]:
    """
    Make a request to an LLM with optional rate limiting
    
    Args:
        prompt_system: System prompt
        prompt_user: User prompt
        model: Model identifier
        response_format: Optional Pydantic model for response structure
        rate_limit: Time between requests in seconds, or None for no rate limiting
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(rate_limit)
        
    provider = LLMProvider(model)
    await _rate_limiter.acquire()
    return await provider.complete(prompt_system, prompt_user, response_format)

__all__ = ['make_request_llm', 'create_structure_class', 'LLMProvider']