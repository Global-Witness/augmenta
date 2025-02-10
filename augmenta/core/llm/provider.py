from typing import Optional, Type, Union
from pydantic import BaseModel
from .instructor_handler import InstructorHandler

class LLMProvider:
    """LiteLLM-based provider implementation with instructor support"""
    
    def __init__(self, model: str):
        self.model = model
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
        
        return await self.instructor.complete_structured(messages, response_format)