from typing import Optional, Type, Union
from pydantic import BaseModel
from .instructor_handler import InstructorHandler
from litellm.utils import trim_messages  # Add this import

class LLMProvider:
    """LiteLLM-based provider implementation with instructor support"""
    
    def __init__(self, model: str, max_tokens: Optional[int] = None):
        self.model = model
        self.max_tokens = max_tokens
        self.instructor = InstructorHandler(model)
        
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
        
        # Trim messages if max_tokens is specified
        messages = trim_messages(messages, self.model, max_tokens=self.max_tokens)
        
        return await self.instructor.complete_structured(messages, response_format)