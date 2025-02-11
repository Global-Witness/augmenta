from typing import Optional, Type, Union, Any
from pydantic import BaseModel
from .provider import LLMProvider
from .instructor_handler import InstructorHandler
from ..utils import RateLimiter

_rate_limiter: Optional[RateLimiter] = None

async def make_request_llm(
    prompt_system: str,
    prompt_user: str,
    model: str,
    response_format: Optional[Type[BaseModel]] = None,
    rate_limit: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> Union[str, dict[str, Any], BaseModel]:
    """
    Make a rate-limited request to an LLM with structured output support.
    
    Args:
        prompt_system: System context for the LLM
        prompt_user: User input/query
        model: LLM model identifier
        response_format: Optional Pydantic model for structured output
        rate_limit: Seconds between requests (None for no limit)
        max_tokens: Maximum tokens in response
        
    Returns:
        String for unstructured responses, dict/BaseModel for structured
        
    Raises:
        ValueError: Invalid prompt or model
        RuntimeError: LLM request failed
    """
    if not prompt_system or not prompt_user:
        raise ValueError("Both system and user prompts are required")
        
    global _rate_limiter
    if rate_limit and not _rate_limiter:
        _rate_limiter = RateLimiter(rate_limit)
        
    if _rate_limiter:
        await _rate_limiter.acquire()
        
    provider = LLMProvider(model, max_tokens)
    return await provider.complete(prompt_system, prompt_user, response_format)

__all__ = ['make_request_llm', 'InstructorHandler', 'LLMProvider']