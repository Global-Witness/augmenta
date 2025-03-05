from typing import Type, Optional, Union, Any, Dict, ClassVar, Literal
from pathlib import Path
from functools import lru_cache
import logging
import yaml
from pydantic import BaseModel, Field, create_model

# Import Agent from pydantic_ai instead of using a custom implementation
from pydantic_ai import Agent

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
        temperature: float = 0.0
    ):
        # Create an Agent with just the temperature setting
        model_settings = {'temperature': temperature}
            
        self.agent = Agent(
            model,
            model_settings=model_settings
        )
        self.model = model

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
        try:
            # Create model_settings for this specific request if temperature is provided
            model_settings = None
            if temperature is not None:
                model_settings = {'temperature': temperature}
                
            # Set the system prompt
            self.agent.system_prompt = prompt_system
            
            # Run the agent with the appropriate parameters
            result = await self.agent.run(
                prompt_user,
                result_type=response_format,
                model_settings=model_settings
            )

            # Return the appropriate result format
            return result.data.model_dump() if response_format else result.data
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {e}")