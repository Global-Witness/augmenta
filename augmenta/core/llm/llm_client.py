from typing import Type, Optional, Union, Any, Dict, ClassVar, Literal
from pathlib import Path
from functools import lru_cache
import logging
import yaml
from pydantic import BaseModel, Field, create_model
import instructor
from tenacity import AsyncRetrying, stop_after_attempt, wait_fixed
from instructor.exceptions import InstructorRetryException

# This gets rid of the LLM costs lookup message
logging.getLogger('httpx').setLevel(logging.WARNING)

from litellm import Router
from litellm.utils import trim_messages

logger = logging.getLogger(__name__)

class LLMClient:
    """Handles LLM interactions with structured output support"""
    
    TYPE_MAPPING: ClassVar[Dict[str, type]] = {
        'str': str, 'bool': bool, 'int': int,
        'float': float, 'dict': dict, 'list': list
    }
    
    def __init__(
        self, 
        model: str, 
        max_tokens: Optional[int] = None,
        max_retries: int = 3,
        retry_wait_seconds: int = 1,
        temperature: float = 0.0  # Added temperature parameter with default 0
    ):
        router = Router(
            model_list=[{
                "model_name": model,
                "litellm_params": {
                    "model": model,
                    "temperature": temperature  # Set temperature in litellm params
                },
            }],
            default_litellm_params={"acompletion": True}
        )
        self.client = instructor.patch(router)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.retry_config = AsyncRetrying(
            stop=stop_after_attempt(max_retries),
            wait=wait_fixed(retry_wait_seconds),
            reraise=True
        )

    @staticmethod
    @lru_cache(maxsize=32)
    def create_structure_class(yaml_file_path: Union[str, Path]) -> Type[BaseModel]:
        """Creates a Pydantic model from YAML structure definition"""
        yaml_file_path = Path(yaml_file_path)
        
        try:
            with open(yaml_file_path, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)
                
            if not isinstance(yaml_content, dict) or 'structure' not in yaml_content:
                raise ValueError("YAML must contain a 'structure' dictionary")
                
            fields: Dict[str, tuple] = {}
            for field_name, field_info in yaml_content['structure'].items():
                if not isinstance(field_info, dict):
                    raise ValueError(f"Invalid field definition for {field_name}")
                
                field_type = (Literal[tuple(str(opt) for opt in field_info['options'])] 
                            if 'options' in field_info 
                            else LLMClient.TYPE_MAPPING.get(field_info.get('type', 'str'), str))
                
                fields[field_name] = (
                    field_type,
                    Field(description=field_info.get('description', ''))
                )
            
            return create_model('Structure', **fields, __base__=BaseModel)
                
        except (yaml.YAMLError, OSError) as e:
            raise ValueError(f"Failed to parse YAML: {e}")

    async def complete(
        self,
        prompt_system: str,
        prompt_user: str,
        response_format: Optional[Type[BaseModel]] = None,
        temperature: Optional[float] = None  # Allow overriding temperature per request
    ) -> Union[str, dict[str, Any], BaseModel]:
        """Generates structured or unstructured completion"""
        messages = [
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user}
        ]
        
        try:
            if self.max_tokens:
                messages = trim_messages(messages, max_tokens=self.max_tokens, model=self.model)
                
            # Use request-specific temperature if provided, otherwise use instance default
            temp = temperature if temperature is not None else self.temperature
                
            if response_format is None:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temp
                )
                return response.choices[0].message.content
            
            result = await self.client.chat.completions.create(
                model=self.model,
                response_model=response_format,
                messages=messages,
                max_retries=self.retry_config,
                temperature=temp
            )
            
            return result.model_dump()
                
        except InstructorRetryException as e:
            logger.error(
                f"Validation error after {e.n_attempts} attempts. "
                f"Last error: {e.messages[-1]['content'] if e.messages else 'Unknown error'}"
            )
            raise RuntimeError(f"LLM request failed after {e.n_attempts} retries: {e}")
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {e}")