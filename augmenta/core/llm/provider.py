from typing import Optional, Type, Union, Any
from pydantic import BaseModel
import logging
from .instructor_handler import InstructorHandler
from litellm.utils import trim_messages

logger = logging.getLogger(__name__)

class LLMProvider:
    """Manages LLM interactions with structured output support"""
    
    def __init__(self, model: str, max_tokens: Optional[int] = None):
        """
        Initialize provider with model settings
        
        Args:
            model: Model identifier
            max_tokens: Maximum response tokens
        """
        self.model = model
        self.max_tokens = max_tokens
        self.instructor = InstructorHandler(model)
        
    async def complete(
        self,
        prompt_system: str,
        prompt_user: str,
        response_format: Optional[Type[BaseModel]] = None
    ) -> Union[str, dict[str, Any], BaseModel]:
        """
        Generate completion with optional structure
        
        Args:
            prompt_system: System context
            prompt_user: User input
            response_format: Optional Pydantic model
            
        Returns:
            Structured or unstructured response
            
        Raises:
            RuntimeError: Completion failed
        """
        messages = [
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user}
        ]
        
        try:
            messages = trim_messages(
                messages,
                max_tokens=self.max_tokens if self.max_tokens else None,
                model=self.model
            )
        except Exception as e:
            logger.warning(f"Message trimming failed: {e}")
        
        return await self.instructor.complete_structured(messages, response_format)