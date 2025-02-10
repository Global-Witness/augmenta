from typing import Optional, Type, Union
from pydantic import BaseModel
from litellm import Router
import instructor
from .validation import OutputValidator

class LLMProvider:
    """LiteLLM-based provider implementation with instructor support"""
    
    def __init__(self, model: str = "openai/gpt-4-turbo-preview"):
        self.model = model
        router = Router(
            model_list=[{
                "model_name": model,
                "litellm_params": {"model": model},
            }],
            default_litellm_params={"acompletion": True}
        )
        self.client = instructor.patch(router)
        self.validator = OutputValidator(model, self.client)
        
    async def complete(
        self,
        prompt_system: str,
        prompt_user: str,
        response_format: Optional[Type[BaseModel]] = None
    ) -> Union[str, dict, BaseModel]:
        """
        Generate completion using LiteLLM with instructor support
        
        Returns:
            Union[str, dict, BaseModel]: String for unstructured responses,
            dict/Pydantic model for structured responses
        """
        messages = [
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user}
        ]
        
        try:
            result = await self.validator.validate_and_parse(messages, response_format)
            return result
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {str(e)}")