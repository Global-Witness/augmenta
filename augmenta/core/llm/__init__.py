from typing import Optional, Type, Union, Any
from pydantic import BaseModel
from .llm_client import LLMClient
from augmenta.utils.utils import RateLimiter

_rate_limiter: Optional[RateLimiter] = None

async def make_request_llm(
    prompt_system: str,
    prompt_user: str,
    model: str,
    response_format: Optional[Type[BaseModel]] = None,
    rate_limit: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> Union[str, dict[str, Any], BaseModel]:
    """Makes a rate-limited request to an LLM with optional structured output."""
    if not prompt_system or not prompt_user:
        raise ValueError("Both system and user prompts are required")
        
    global _rate_limiter
    if rate_limit and not _rate_limiter:
        _rate_limiter = RateLimiter(rate_limit)
        
    if _rate_limiter:
        await _rate_limiter.acquire()
        
    client = LLMClient(model, max_tokens)
    return await client.complete(prompt_system, prompt_user, response_format)

__all__ = ['make_request_llm', 'LLMClient']