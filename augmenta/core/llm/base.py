from typing import Type, Optional, Union, Any, Dict, ClassVar, Literal
from pathlib import Path
import yaml
from pydantic import BaseModel, Field, create_model
from pydantic_ai import Agent
from pydantic_ai.usage import UsageLimits
import logfire
from pydantic_ai import Agent

logfire.configure(scrubbing=False)
# Instrument all PydanticAI agents with logfire
Agent.instrument_all()

class BaseAgent:
    """Base class providing core LLM functionality"""
    
    TYPE_MAPPING: ClassVar[Dict[str, type]] = {
        'str': str, 'bool': bool, 'int': int,
        'float': float, 'dict': dict, 'list': list
    }
    
    def __init__(
        self, 
        model: str, 
        temperature: float = 0.0,
        rate_limit: Optional[float] = None,
        max_tokens: Optional[int] = None,
        verbose: bool = False
    ):
        """Initialize the base agent.
        
        Args:
            model: The LLM model identifier
            temperature: Temperature setting for the model
            rate_limit: Optional rate limit between requests
            max_tokens: Optional maximum tokens for response
            verbose: Whether to enable verbose logging with logfire
        """
        # Create model settings with all available parameters
        model_settings = {'temperature': temperature}
        if rate_limit is not None:
            model_settings['rate_limit'] = rate_limit
        if max_tokens is not None:
            model_settings['max_tokens'] = max_tokens
            
        self.agent = Agent(
            model,
            model_settings=model_settings
        )
        self.model = model
        self.temperature = temperature
        self.rate_limit = rate_limit
        self.max_tokens = max_tokens
        self.verbose = verbose

    @staticmethod
    def create_structure_class(yaml_file_path: Union[str, Path]) -> Type[BaseModel]:
        """Creates a Pydantic model from YAML structure definition.
        
        Args:
            yaml_file_path: Path to YAML file containing structure definition
            
        Returns:
            A Pydantic model class based on the YAML structure
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
                
                field_type = (Literal[tuple(str(opt) for opt in field_info['options'])] 
                           if 'options' in field_info 
                           else BaseAgent.TYPE_MAPPING.get(field_info.get('type', 'str'), str))
                
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
        """Generates structured or unstructured completion.
        
        Args:
            prompt_system: System prompt for the LLM
            prompt_user: User prompt/query
            response_format: Optional Pydantic model for structured output
            temperature: Optional override for model temperature
            
        Returns:
            Either a string, dict, or Pydantic model depending on response_format
        """
        try:
            # Create model_settings for this specific request if temperature is provided
            model_settings = None
            if temperature is not None:
                model_settings = {'temperature': temperature}
                if self.rate_limit is not None:
                    model_settings['rate_limit'] = self.rate_limit
                if self.max_tokens is not None:
                    model_settings['max_tokens'] = self.max_tokens
                
            # Set the system prompt
            self.agent.system_prompt = prompt_system
            
            # Run the agent with the appropriate parameters
            result = await self.agent.run(
                prompt_user,
                result_type=response_format,
                model_settings=model_settings,
                usage_limits=UsageLimits(request_limit=5)
            )

            # Return the appropriate result format
            return result.data.model_dump() if response_format else result.data
        except Exception as e:
            logfire.error(f"LLM request failed: {e}")
            raise RuntimeError(f"LLM request failed: {e}")

async def make_request_llm(
    prompt_system: str,
    prompt_user: str,
    model: str,
    response_format: Optional[Type[BaseModel]] = None,
    rate_limit: Optional[float] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    verbose: bool = False
) -> Union[str, Dict[str, Any], BaseModel]:
    """Make a request to the LLM.
    
    Args:
        prompt_system: System prompt for the LLM
        prompt_user: User prompt/query
        model: Model identifier in format "provider:name"
        response_format: Optional Pydantic model for structured output
        rate_limit: Optional rate limit between requests
        max_tokens: Optional maximum tokens for response
        temperature: Optional temperature setting for the model
        verbose: Whether to enable verbose logging
        
    Returns:
        The model's response in the appropriate format
    """
    agent = BaseAgent(
        model=model,
        temperature=temperature if temperature is not None else 0.0,
        rate_limit=rate_limit,
        max_tokens=max_tokens,
        verbose=verbose
    )
    
    return await agent.complete(
        prompt_system=prompt_system,
        prompt_user=prompt_user,
        response_format=response_format
    )