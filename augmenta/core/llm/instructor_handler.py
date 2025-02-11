from typing import Type, Optional, Union, Literal, get_args
from pathlib import Path
from pydantic import BaseModel, create_model, Field
import yaml
import instructor
from litellm import Router

class InstructorHandler:
    """Centralized handler for instructor-based structured output processing"""
    
    def __init__(self, model: str):
        """Initialize the instructor handler with a specific model"""
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
    def create_structure_class(yaml_file_path: Union[str, Path]) -> Type[BaseModel]:
        """Creates a Pydantic model class from YAML structure"""
        TYPE_MAPPING = {
            'str': str,
            'bool': bool,
            'int': int,
            'float': float,
            'dict': dict,
            'list': list,
        }
        
        yaml_file_path = Path(yaml_file_path)
        try:
            with open(yaml_file_path, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)
                
            if 'structure' not in yaml_content:
                raise KeyError("YAML file must contain a 'structure' key")
                
            fields = {}
            for field_name, field_info in yaml_content['structure'].items():
                field_type = TYPE_MAPPING.get(field_info['type'], str)
                description = field_info.get('description', '')
                
                # Handle options field by creating a Literal type
                if 'options' in field_info:
                    options = tuple(field_info['options'])
                    field_type = Literal[options]  # type: ignore
                
                fields[field_name] = (
                    field_type, 
                    Field(
                        default=None, 
                        description=description,
                        # Include options in field metadata if present
                        json_schema_extra={
                            'options': field_info['options']
                        } if 'options' in field_info else None
                    )
                )
            
            StructureClass = create_model('Structure', **fields, __base__=BaseModel)
            
            # Add validation to ensure values match options
            for field_name, field_info in yaml_content['structure'].items():
                if 'options' in field_info:
                    field = StructureClass.model_fields[field_name]
                    field.json_schema_extra = {
                        'options': field_info['options']
                    }
            
            return StructureClass
            
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")

    async def complete_structured(
        self,
        messages: list,
        response_format: Optional[Type[BaseModel]] = None
    ) -> Union[str, dict, BaseModel]:
        """
        Generate a structured completion using instructor
        
        Args:
            messages: List of message dictionaries
            response_format: Optional Pydantic model for response structure
            
        Returns:
            Union[str, dict, BaseModel]: Structured response based on the provided format
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
            
            return result.model_dump()
                
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {str(e)}")