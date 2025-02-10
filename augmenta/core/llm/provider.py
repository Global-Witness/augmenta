from typing import Optional, Type, Any
from pydantic import BaseModel
import litellm
import instructor
from litellm import Router, get_supported_openai_params, supports_response_schema

class LLMProvider:
    """LiteLLM-based provider implementation with instructor and native JSON support"""
    
    def __init__(self, model: str = "openai/gpt-4-turbo-preview"):
        self.model = model
        # Create a router with async support
        router = Router(
            model_list=[{
                "model_name": model,
                "litellm_params": {"model": model},
            }],
            default_litellm_params={"acompletion": True}
        )
        # Patch the router with instructor
        self.client = instructor.patch(router)
        
        # Check model capabilities
        self.supported_params = get_supported_openai_params(model)
        self.supports_json_schema = supports_response_schema(model)
        
    async def complete(
        self,
        prompt_system: str,
        prompt_user: str,
        response_format: Optional[Type[BaseModel]] = None
    ) -> Any:
        """Generate completion using LiteLLM with optimal structured output support"""
        messages = [
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user}
        ]
        
        try:
            if response_format is not None:
                if "response_format" in self.supported_params and self.supports_json_schema:
                    # Use native JSON schema support
                    response = await litellm.acompletion(
                        model=self.model,
                        messages=messages,
                        response_format={
                            "type": "json_schema",
                            "schema": response_format.model_json_schema(),
                            "strict": True
                        }
                    )
                    # Parse the JSON response into the Pydantic model
                    return response_format.model_validate_json(
                        response.choices[0].message.content
                    )
                else:
                    # Fallback to instructor for models without native support
                    return await self.client.chat.completions.create(
                        model=self.model,
                        response_model=response_format,
                        messages=messages
                    )
            else:
                # Regular completion without structured output
                response = await litellm.acompletion(
                    model=self.model,
                    messages=messages
                )
                return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {str(e)}")