from typing import Type, Optional, Union, Any, Dict, ClassVar, Literal
from pathlib import Path
from functools import lru_cache
from pydantic import BaseModel, Field, create_model
import yaml
import instructor
from litellm import Router

class InstructorHandler:
    """Handles structured output processing using instructor"""
    
    # Type mapping for YAML to Python types
    TYPE_MAPPING: ClassVar[Dict[str, type]] = {
        'str': str, 'bool': bool, 'int': int,
        'float': float, 'dict': dict, 'list': list
    }
    
    def __init__(self, model: str):
        """
        Initialize with model configuration
        
        Args:
            model: Model identifier
        """
        router = Router(
            model_list=[{
                "model_name": model,
                "litellm_params": {"model": model},
            }],
            default_litellm_params={"acompletion": True}
        )
        self.client = instructor.patch(router)
        self.model = model

    @staticmethod
    @lru_cache(maxsize=32)
    def create_structure_class(yaml_file_path: Union[str, Path]) -> Type[BaseModel]:
        """
        Creates a cached Pydantic model from YAML structure
        
        Args:
            yaml_file_path: Path to YAML structure definition
            
        Returns:
            Pydantic model class
            
        Raises:
            ValueError: Invalid YAML or structure
        """
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
                
                # Handle options field by creating a Literal type
                if 'options' in field_info:
                    options = tuple(str(opt) for opt in field_info['options'])
                    field_type = Literal[options]
                else:
                    field_type = InstructorHandler.TYPE_MAPPING.get(
                        field_info.get('type', 'str'),
                        str
                    )
                
                fields[field_name] = (
                    field_type,
                    Field(description=field_info.get('description', ''))
                )
            
            return create_model('Structure', **fields, __base__=BaseModel)
                
        except (yaml.YAMLError, OSError) as e:
            raise ValueError(f"Failed to parse YAML: {e}")

    async def complete_structured(
        self,
        messages: list[dict[str, str]],
        response_format: Optional[Type[BaseModel]] = None
    ) -> Union[str, dict[str, Any], BaseModel]:
        """
        Generate structured or unstructured completion
        
        Args:
            messages: List of role/content message pairs
            response_format: Optional Pydantic model for structure
            
        Returns:
            Structured or unstructured response
            
        Raises:
            RuntimeError: Request or parsing failed
        """
        try:
            if response_format is None:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
                return response.choices[0].message.content
            
            result = await self.client.chat.completions.create(
                model=self.model,
                response_model=response_format,
                messages=messages
            )
            
            return result.model_dump()
                
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {e}")