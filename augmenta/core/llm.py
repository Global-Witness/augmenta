"""
LLM interaction module for handling structured responses and model communication.
Provides utilities for creating Pydantic models from YAML and making LLM requests.
"""

import yaml
from typing import Type, Optional, Dict, Any
from pydantic import BaseModel, Field, create_model
from litellm import acompletion, ModelResponse
from dotenv import load_dotenv

# Load environment variables at module initialization
load_dotenv()

# Type aliases for clarity
YAMLStructure = Dict[str, Dict[str, Any]]
ModelClass = Type[BaseModel]

# Mapping of YAML types to Python types
TYPE_MAPPING = {
    'str': str,
    'bool': bool,
    'ConfidenceLevel': str,
    # Add more type mappings as needed
}

def create_structure_class(yaml_file_path: str) -> ModelClass:
    """
    Creates a Pydantic model class from a YAML structure definition.
    
    Args:
        yaml_file_path: Path to the YAML file containing structure definition
        
    Returns:
        A Pydantic model class with the defined structure
        
    Raises:
        FileNotFoundError: If YAML file doesn't exist
        yaml.YAMLError: If YAML file is malformed
        KeyError: If required 'structure' key is missing in YAML
    """
    try:
        with open(yaml_file_path, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)
            
        if 'structure' not in yaml_content:
            raise KeyError("YAML file must contain a 'structure' key")
            
        fields = {
            field_name: (
                TYPE_MAPPING.get(field_info['type'], str),
                Field(description=field_info['description'])
            )
            for field_name, field_info in yaml_content['structure'].items()
        }
        
        return create_model('Structure', **fields, __base__=BaseModel)
        
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file: {e}")

async def make_request_llm(
    prompt_system: str, 
    prompt_user: str, 
    model: str = "openai/gpt-4-turbo-preview", 
    response_format: Optional[ModelClass] = None
) -> str:
    """
    Makes an async request to LLM models with structured prompts.
    
    Args:
        prompt_system: System prompt for context setting
        prompt_user: User prompt containing the actual query
        model: Model identifier string
        response_format: Optional Pydantic model for response structure
        
    Returns:
        Model response content as string
        
    Raises:
        Exception: If LLM request fails
    """
    completion_args = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user}
        ]
    }
    
    if response_format is not None:
        completion_args["response_format"] = response_format
    
    try:
        response: ModelResponse = await acompletion(**completion_args)
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"LLM request failed: {str(e)}")