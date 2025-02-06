from typing import Optional, Type, Any
from pydantic import BaseModel
import litellm
from .base import LLMProvider

class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation"""
    
    def __init__(self, model: str = "openai/gpt-4-turbo-preview"):
        self.model = model
        
    async def complete(
        self,
        prompt_system: str,
        prompt_user: str,
        response_format: Optional[Type[BaseModel]] = None
    ) -> Any:
        """Generate completion using OpenAI"""
        completion_args = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user}
            ]
        }
        
        if response_format is not None:
            completion_args["response_format"] = response_format
        
        try:
            response = await litellm.acompletion(**completion_args)
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {str(e)}")