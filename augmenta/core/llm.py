import warnings

# TODO: Remove after https://github.com/BerriAI/litellm/issues/7560 is fixed
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic._internal._config")



import yaml
from pydantic import BaseModel, Field, create_model
from typing import Type
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

def create_structure_class(yaml_file_path) -> Type[BaseModel]:
    """Creates a Pydantic model class from YAML structure definition."""
    with open(yaml_file_path, 'r') as f:
        yaml_content = yaml.safe_load(f)
    
    fields = {}
    for field_name, field_info in yaml_content['structure'].items():
        # Convert YAML types to Python types
        field_type = {
            'str': str,
            'bool': bool,
            'ConfidenceLevel': str  # Assuming ConfidenceLevel should be string
        }.get(field_info['type'], str)
        
        fields[field_name] = (field_type, Field(description=field_info['description']))
    
    return create_model('Structure', **fields, __base__=BaseModel)

def make_request_llm(prompt_system: str, prompt_user: str, model: str = "openai/gpt-4o-mini", response_format=None):
    """
    Make a request to LLM models.
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
    
    response = completion(**completion_args)

    return response.choices[0].message.content