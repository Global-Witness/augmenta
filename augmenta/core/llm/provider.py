from typing import Optional, Type, Union
from pydantic import BaseModel
from .instructor_handler import InstructorHandler
from litellm.utils import trim_messages
import logging

logger = logging.getLogger(__name__)

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
        
        try:
            # Trim messages based on whether max_tokens is specified
            if self.max_tokens is not None:
                messages = trim_messages(messages, max_tokens=self.max_tokens)
            else:
                messages = trim_messages(messages, model=self.model)
        except Exception as e:
            logger.warning("Message trimming failed, using original messages.")
        
        return await self.instructor.complete_structured(messages, response_format)