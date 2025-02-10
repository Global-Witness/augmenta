from typing import Optional, Type, Union, Any
from pydantic import BaseModel
import instructor

class OutputValidator:
    """Handles structured output validation and parsing for LLM responses"""

    def __init__(self, model: str, client: Any):
        self.model = model
        self.client = client

    async def validate_and_parse(
        self,
        messages: list,
        response_format: Optional[Type[BaseModel]] = None
    ) -> Union[str, dict, BaseModel]:
        """
        Validate and parse LLM response according to the specified format
        
        Args:
            messages: List of message dictionaries
            response_format: Optional Pydantic model for response structure
            
        Returns:
            Union[str, dict, BaseModel]: Either a string for unstructured responses,
            or a dictionary/Pydantic model for structured responses
        """
        try:
            if response_format is None:
                # Regular completion without structured output
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
                return response.choices[0].message.content
            
            # Use instructor for structured output
            result = await self.client.chat.completions.create(
                model=self.model,
                response_model=response_format,
                messages=messages
            )
            
            # Convert Pydantic model to dict
            return result.model_dump()
                
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {str(e)}")