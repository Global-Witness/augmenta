from typing import Type
from pydantic import BaseModel, create_model
import yaml

def create_structure_class(yaml_file_path: str) -> Type[BaseModel]:
    """Creates a Pydantic model class from YAML structure"""
    TYPE_MAPPING = {
        'str': str,
        'bool': bool,
        'ConfidenceLevel': str,
        'int': int,
        'float': float,
        'dict': dict,
        'list': list,
    }
    
    try:
        with open(yaml_file_path, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)
            
        if 'structure' not in yaml_content:
            raise KeyError("YAML file must contain a 'structure' key")
            
        fields = {
            field_name: (
                TYPE_MAPPING.get(field_info['type'], str),
                (None, ...)  # (default, required)
            )
            for field_name, field_info in yaml_content['structure'].items()
        }
        
        return create_model('Structure', **fields, __base__=BaseModel)
        
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")