from typing import Optional, Type, Union, Any
from pydantic import BaseModel
from .llm_client import LLMClient
from augmenta.utils.limiter import RateLimitManager

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
    
    client = LLMClient(model, max_tokens)
    
    if rate_limit:
        # Convert rate_limit from seconds to requests per second
        rate = 1.0 / rate_limit if rate_limit else None
        async with RateLimitManager.acquire("LLMClient", rate):
            return await client.complete(prompt_system, prompt_user, response_format)
    else:
        return await client.complete(prompt_system, prompt_user, response_format)

__all__ = ['make_request_llm', 'LLMClient']